#!/usr/bin/env python3
"""Main entry point for GitHub Opportunity Scraper."""

import os
import sys
from pathlib import Path
from typing import Optional, List
import yaml
import urllib.parse
import urllib.request
from dotenv import load_dotenv
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from src.github_fetcher import GitHubFetcher
from src.analyzer import OpportunityAnalyzer
from src.output import OutputWriter
from src.models import GitHubIssue, OpportunityAnalysis
from src.exceptions import GitHubRateLimitExceeded, GeminiRateLimitExceeded

# Load environment variables
load_dotenv()

app = typer.Typer(help="GitHub Opportunity Scraper - Find business opportunities in open source projects")
console = Console()


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    config_file = Path(config_path)
    if not config_file.exists():
        console.print(f"[red]Error: Config file not found: {config_path}[/red]")
        sys.exit(1)
    
    with open(config_file, "r") as f:
        return yaml.safe_load(f)


def send_notification(opportunity_count: int, notification_url: Optional[str] = None, user_name: str = "GitHub Scraper") -> None:
    """
    Send notification when opportunities are found.
    
    Args:
        opportunity_count: Number of opportunities found
        notification_url: URL to send notification to (from env var NOTIFICATION_URL)
        user_name: Name to include in notification message
    """
    if not notification_url:
        notification_url = os.getenv("NOTIFICATION_URL")
    
    if not notification_url:
        return  # No notification URL configured, silently skip
    
    if opportunity_count == 0:
        return  # Only notify when opportunities are found
    
    try:
        # Format message: "Found X opportunities, Your Name"
        message = f"Found {opportunity_count} opportunities, {user_name}"
        
        # Encode message for URL
        encoded_msg = urllib.parse.quote(message)
        
        # Build URL with query parameter
        url = f"{notification_url.rstrip('/')}?msg={encoded_msg}"
        
        # Send GET request
        with urllib.request.urlopen(url, timeout=10) as response:
            if response.status == 200:
                console.print(f"[green]✓ Notification sent successfully[/green]")
            else:
                console.print(f"[yellow]⚠ Notification sent but received status {response.status}[/yellow]")
    except urllib.error.URLError as e:
        console.print(f"[yellow]⚠ Failed to send notification: {e}[/yellow]")
    except Exception as e:
        console.print(f"[yellow]⚠ Error sending notification: {e}[/yellow]")


@app.command()
def run(
    repos: Optional[str] = typer.Option(None, "--repos", "-r", help="Comma-separated list of repositories (e.g., 'facebook/react,vercel/next.js')"),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Programming language filter"),
    min_stars: Optional[int] = typer.Option(None, "--min-stars", "-s", help="Minimum stars for repository search"),
    labels: Optional[str] = typer.Option(None, "--labels", help="Comma-separated list of labels to filter"),
    config_file: str = typer.Option("config.yaml", "--config", "-c", help="Path to config file"),
):
    """Run the opportunity scraper."""
    
    # Display banner
    banner = Text("GitHub Opportunity Scraper", style="bold cyan")
    console.print(Panel(banner, border_style="cyan"))
    console.print()
    
    # Load configuration
    config = load_config(config_file)
    
    # Override config with CLI arguments
    if repos:
        config["repositories"] = [r.strip() for r in repos.split(",")]
    if language:
        config["search"]["language"] = language
    if min_stars:
        config["search"]["min_stars"] = min_stars
    if labels:
        config["issues"]["labels"] = [l.strip() for l in labels.split(",")]
    
    # Get API keys
    github_token = os.getenv("GITHUB_TOKEN")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    if not gemini_api_key:
        console.print("[red]Error: GEMINI_API_KEY environment variable not set[/red]")
        console.print("[yellow]Get your API key at: https://aistudio.google.com/apikey[/yellow]")
        sys.exit(1)
    
    # Initialize components
    try:
        github_fetcher = GitHubFetcher(
            token=github_token,
            rate_limit_delay=config["rate_limits"]["delay_between_requests"],
            cache_file=config["output"].get("cache_file", "output/searched_repos.json")
        )
    except GitHubRateLimitExceeded as exc:
        console.print(f"[red]GitHub rate limit exceeded during initialization: {exc}[/red]")
        sys.exit(1)

    analyzer = OpportunityAnalyzer(
        api_key=gemini_api_key,
        model=config["analysis"]["model"],
        fallback_model=config["analysis"]["fallback_model"],
        temperature=config["analysis"]["temperature"],
        requests_per_minute=config["rate_limits"]["gemini_requests_per_minute"]
    )
    
    output_writer = OutputWriter(output_dir=config["output"]["directory"])
    
    try:
        # Fetch repositories
        console.print("[bold]Step 1: Fetching repositories...[/bold]")
        repositories = []
        
        if config["repositories"]:
            # Use specified repositories
            console.print(f"Using {len(config['repositories'])} specified repositories")
            for repo_name in config["repositories"]:
                try:
                    # Skip if already searched
                    if github_fetcher.is_repo_searched(repo_name):
                        console.print(f"[cyan]Skipping {repo_name} (already searched)[/cyan]")
                        continue
                    
                    repo = github_fetcher.get_repository(repo_name)
                    if not github_fetcher._is_tool_repository(repo):  # type: ignore[attr-defined]
                        console.print(f"[yellow]Skipping {repo_name} (looks like documentation/course/list repository)[/yellow]")
                        continue
                    repositories.append(repo)
                except GitHubRateLimitExceeded:
                    raise
                except Exception as e:
                    console.print(f"[red]Error fetching {repo_name}: {e}[/red]")
        else:
            # Search for repositories
            repositories = github_fetcher.search_repositories(
                language=config["search"]["language"] or None,
                min_stars=config["search"]["min_stars"],
                sort=config["search"]["sort"],
                limit=10
            )
        
        if not repositories:
            console.print("[red]No repositories found. Exiting.[/red]")
            sys.exit(1)
        
        # Fetch issues
        console.print(f"\n[bold]Step 2: Fetching issues from {len(repositories)} repositories...[/bold]")
        all_issues: List[GitHubIssue] = []
        
        for repo in repositories:
            issues = github_fetcher.fetch_issues(
                repo=repo,
                labels=config["issues"]["labels"],
                state=config["issues"]["state"],
                min_reactions=config["issues"]["min_reactions"],
                min_comments=config["issues"]["min_comments"],
                max_issues=config["issues"]["max_issues_per_repo"]
            )
            all_issues.extend(issues)
        
        if not all_issues:
            console.print("[yellow]No issues found matching criteria. Exiting.[/yellow]")
            sys.exit(0)
        
        console.print(f"[green]Found {len(all_issues)} total issues[/green]")
        
        # Analyze issues
        console.print(f"\n[bold]Step 3: Analyzing issues with {config['analysis']['model']}...[/bold]")
        
        # Analyze each issue and collect matching pairs
        analyzed_issues: List[GitHubIssue] = []
        valid_analyses: List[OpportunityAnalysis] = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Analyzing issues...", total=len(all_issues))
            
            for issue in all_issues:
                analysis = analyzer.analyze_issue(issue)
                if analysis and analysis.total_score >= config["analysis"]["min_opportunity_score"]:
                    analyzed_issues.append(issue)
                    valid_analyses.append(analysis)
                
                progress.update(
                    task,
                    advance=1,
                    description=f"Analyzed {progress.tasks[0].completed}/{len(all_issues)} issues, found {len(analyzed_issues)} opportunities"
                )
        
        if not analyzed_issues:
            console.print("[yellow]No high-scoring opportunities found (score >= {})[/yellow]".format(
                config["analysis"]["min_opportunity_score"]
            ))
            sys.exit(0)
        
        # Write output
        console.print(f"\n[bold]Step 4: Writing output...[/bold]")
        output_writer.write_json(
            issues=analyzed_issues,
            analyses=valid_analyses,
            filename=config["output"]["json_filename"],
            sort_by=config["output"]["sort_by"]
        )
        
        output_writer.write_csv(
            issues=analyzed_issues,
            analyses=valid_analyses,
            filename=config["output"]["csv_filename"],
            sort_by=config["output"]["sort_by"]
        )
        
        # Summary
        console.print()
        console.print(Panel(
            f"[green]✓ Complete![/green]\n\n"
            f"Found [bold]{len(analyzed_issues)}[/bold] opportunities\n"
            f"Output written to: [cyan]{config['output']['directory']}/[/cyan]",
            title="Summary",
            border_style="green"
        ))
        
        # Send notification if opportunities found
        if len(analyzed_issues) > 0:
            user_name = os.getenv("USER_NAME", os.getenv("USER", "GitHub Scraper"))
            notification_url = os.getenv("NOTIFICATION_URL")
            send_notification(len(analyzed_issues), notification_url=notification_url, user_name=user_name)

    except GitHubRateLimitExceeded as exc:
        console.print(f"[red]GitHub rate limit exceeded: {exc}[/red]")
        console.print("[yellow]Stopping early to avoid hitting GitHub's request cap. Try again later or reduce the search scope.[/yellow]")
        sys.exit(1)
    except GeminiRateLimitExceeded as exc:
        console.print(f"[red]Gemini rate limit exceeded: {exc}[/red]")
        console.print("[yellow]Stopping early to stay within Gemini rate limits. Try lowering max issues per repo or waiting before retrying.[/yellow]")
        sys.exit(1)


@app.command()
def check():
    """Check API keys and configuration."""
    console.print("[bold]Checking configuration...[/bold]\n")
    
    # Check environment variables
    github_token = os.getenv("GITHUB_TOKEN")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    notification_url = os.getenv("NOTIFICATION_URL")
    user_name = os.getenv("USER_NAME")
    
    if github_token:
        console.print("[green]✓ GITHUB_TOKEN is set[/green]")
    else:
        console.print("[yellow]⚠ GITHUB_TOKEN not set (optional, but recommended for higher rate limits)[/yellow]")
    
    if gemini_api_key:
        console.print("[green]✓ GEMINI_API_KEY is set[/green]")
    else:
        console.print("[red]✗ GEMINI_API_KEY not set (required)[/red]")
        console.print("[yellow]Get your API key at: https://aistudio.google.com/apikey[/yellow]")
    
    if notification_url:
        console.print(f"[green]✓ NOTIFICATION_URL is set[/green]")
        console.print(f"   URL: {notification_url}")
    else:
        console.print("[yellow]⚠ NOTIFICATION_URL not set (optional - notifications disabled)[/yellow]")
    
    if user_name:
        console.print(f"[green]✓ USER_NAME is set: {user_name}[/green]")
    else:
        default_name = os.getenv("USER", "GitHub Scraper")
        console.print(f"[yellow]⚠ USER_NAME not set (will use: {default_name})[/yellow]")
    
    # Check config file
    config_path = Path("config.yaml")
    if config_path.exists():
        console.print("[green]✓ config.yaml exists[/green]")
    else:
        console.print("[red]✗ config.yaml not found[/red]")
    
    # Check output directory
    output_dir = Path("output")
    if output_dir.exists():
        console.print("[green]✓ output/ directory exists[/green]")
    else:
        console.print("[yellow]⚠ output/ directory will be created automatically[/yellow]")


if __name__ == "__main__":
    app()

