"""AI analyzer using Google Gemini API to score GitHub issues as business opportunities."""

import time
from typing import List, Optional
from google import genai
from google.genai import types
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from .models import GitHubIssue, OpportunityAnalysis
from .exceptions import GeminiRateLimitExceeded

try:
    from google.genai.errors import RateLimitError  # type: ignore
except ImportError:  # pragma: no cover
    RateLimitError = None  # type: ignore

try:
    from google.api_core.exceptions import ResourceExhausted  # type: ignore
except ImportError:  # pragma: no cover
    ResourceExhausted = None  # type: ignore

console = Console()

# System prompt for opportunity analysis
SYSTEM_PROMPT = """You are an expert software business analyst specializing in identifying 
market opportunities from open source project issues and feature requests.

Your task is to analyze GitHub issues and determine if they represent a viable 
business opportunity - something that could be built as a standalone product or SaaS.

For each issue, evaluate:
1. MARKET_POTENTIAL (1-10): How many developers/companies face this problem?
2. TECHNICAL_FEASIBILITY (1-10): Can this be built as a standalone tool/product?
3. COMPETITION (1-10): 10 = no existing solutions, 1 = saturated market
4. MONETIZATION_FIT (1-10): How suitable for SaaS/paid tool model?

Consider:
- Issue engagement (reactions, comments) indicates real demand
- Recurring themes across repos suggest market gaps
- Complex integrations often deter existing solutions
- Developer tooling and automation have strong SaaS potential

Be critical - most issues are NOT business opportunities. Only high-scoring 
issues (total >= 25/40) are worth pursuing.

Return your analysis as JSON matching the OpportunityAnalysis schema."""


class OpportunityAnalyzer:
    """Analyzes GitHub issues using Gemini AI to identify business opportunities."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        fallback_model: str = "gemini-2.0-flash-001",
        temperature: float = 0.3,
        requests_per_minute: int = 12
    ):
        """
        Initialize the analyzer.
        
        Args:
            api_key: Google Gemini API key
            model: Primary model to use
            fallback_model: Fallback model if primary fails
            temperature: Model temperature (0.0-1.0)
            requests_per_minute: Rate limit (default 12 to stay under 15 RPM free tier)
        """
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.fallback_model = fallback_model
        self.temperature = temperature
        self.requests_per_minute = requests_per_minute
        self.min_delay = 60.0 / requests_per_minute  # Minimum seconds between requests
        self.last_request_time = 0.0

    @staticmethod
    def _is_rate_limit_error(error: Exception) -> bool:
        """Determine whether the provided error is a Gemini rate limit error."""
        if RateLimitError is not None and isinstance(error, RateLimitError):
            return True

        if ResourceExhausted is not None and isinstance(error, ResourceExhausted):
            return True

        code = getattr(error, "code", None)
        if isinstance(code, int) and code == 429:
            return True

        if isinstance(code, str) and code.upper() == "RESOURCE_EXHAUSTED":
            return True

        message = str(error).lower()
        return any(keyword in message for keyword in ("rate limit", "quota", "resource exhausted"))
    
    def _rate_limit(self) -> None:
        """Enforce rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _create_prompt(self, issue: GitHubIssue) -> str:
        """Create analysis prompt from GitHub issue."""
        return f"""Analyze this GitHub issue:

Repository: {issue.repo_full_name}
Issue #{issue.issue_number}: {issue.title}

Description:
{issue.body[:2000]}  # Truncate if too long

Engagement Metrics:
- Reactions: {issue.reactions}
- Comments: {issue.comments}
- Labels: {', '.join(issue.labels)}
- Created: {issue.created_at.strftime('%Y-%m-%d')}
- Last Updated: {issue.updated_at.strftime('%Y-%m-%d')}

URL: {issue.url}

Analyze this issue and provide scores for market potential, technical feasibility, 
competition, and monetization fit. Be honest - most issues are NOT business opportunities."""
    
    @staticmethod
    def _ensure_total_score(analysis: OpportunityAnalysis) -> OpportunityAnalysis:
        """Ensure total_score is populated even if the model omits it."""
        total = getattr(analysis, "total_score", None)
        # Only recalculate if total_score is None or not an integer
        # Note: total == 0 is impossible since all scores have ge=1 constraint (min total = 4)
        if not isinstance(total, int):
            # Use actual field values (guaranteed >= 1 by model constraints)
            analysis.total_score = (
                analysis.market_potential +
                analysis.technical_feasibility +
                analysis.competition +
                analysis.monetization_fit
            )
        return analysis

    def analyze_issue(self, issue: GitHubIssue) -> Optional[OpportunityAnalysis]:
        """
        Analyze a single GitHub issue.
        
        Args:
            issue: GitHubIssue to analyze
            
        Returns:
            OpportunityAnalysis or None if analysis fails
        """
        self._rate_limit()
        
        prompt = self._create_prompt(issue)
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type='application/json',
                    response_schema=OpportunityAnalysis,
                    temperature=self.temperature,
                ),
            )
            
            # Parse response
            analysis = response.parsed
            if analysis is None:
                return None
            
            return self._ensure_total_score(analysis)
            
        except Exception as e:
            if self._is_rate_limit_error(e):
                raise GeminiRateLimitExceeded("Gemini API rate limit exceeded") from e

            console.print(f"[red]Error analyzing issue #{issue.issue_number} from {issue.repo}: {e}[/red]")
            
            # Try fallback model if primary fails
            if self.model != self.fallback_model:
                try:
                    console.print(f"[yellow]Trying fallback model: {self.fallback_model}[/yellow]")
                    self._rate_limit()
                    fallback_response = self.client.models.generate_content(
                        model=self.fallback_model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            response_mime_type='application/json',
                            response_schema=OpportunityAnalysis,
                            temperature=self.temperature,
                        ),
                    )
                    fallback_analysis = fallback_response.parsed
                    if fallback_analysis is None:
                        return None
                    return self._ensure_total_score(fallback_analysis)
                except Exception as e2:
                    if self._is_rate_limit_error(e2):
                        raise GeminiRateLimitExceeded("Gemini API rate limit exceeded") from e2
                    console.print(f"[red]Fallback model also failed: {e2}[/red]")
            
            return None
    
    def analyze_issues(
        self,
        issues: List[GitHubIssue],
        min_score: int = 25,
        show_progress: bool = True
    ) -> List[OpportunityAnalysis]:
        """
        Analyze multiple issues and return only high-scoring opportunities.
        
        Args:
            issues: List of GitHubIssue objects
            min_score: Minimum total score to include
            show_progress: Whether to show progress bar
            
        Returns:
            List of OpportunityAnalysis objects with score >= min_score
        """
        opportunities = []
        
        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                task = progress.add_task("Analyzing issues...", total=len(issues))
                
                for issue in issues:
                    analysis = self.analyze_issue(issue)
                    if analysis and analysis.total_score >= min_score:
                        opportunities.append(analysis)
                    
                    progress.update(task, advance=1, description=f"Analyzed {progress.tasks[0].completed}/{len(issues)} issues, found {len(opportunities)} opportunities")
        else:
            for issue in issues:
                analysis = self.analyze_issue(issue)
                if analysis and analysis.total_score >= min_score:
                    opportunities.append(analysis)
        
        console.print(f"[green]Analysis complete: {len(opportunities)} opportunities found (score >= {min_score})[/green]")
        return opportunities

