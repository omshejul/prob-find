"""GitHub API integration for fetching repositories and issues."""

import os
import time
from typing import List, Optional
from github import Github
from github.Repository import Repository
from github.Issue import Issue
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .models import GitHubIssue

console = Console()


class GitHubFetcher:
    """Fetches repositories and issues from GitHub API."""
    
    def __init__(self, token: Optional[str] = None, rate_limit_delay: float = 0.1):
        """
        Initialize GitHub fetcher.
        
        Args:
            token: GitHub personal access token (optional but recommended)
            rate_limit_delay: Delay between requests in seconds
        """
        self.github = Github(token) if token else Github()
        self.rate_limit_delay = rate_limit_delay
        self._check_rate_limit()
    
    def _check_rate_limit(self) -> None:
        """Check and display current rate limit status."""
        rate_limit = self.github.get_rate_limit()
        remaining = rate_limit.core.remaining
        reset_time = rate_limit.core.reset
        
        if remaining < 100:
            console.print(f"[yellow]Warning: Only {remaining} GitHub API requests remaining. Resets at {reset_time}[/yellow]")
        else:
            console.print(f"[green]GitHub API: {remaining} requests remaining[/green]")
    
    def _rate_limit_delay(self) -> None:
        """Apply rate limiting delay."""
        if self.rate_limit_delay > 0:
            time.sleep(self.rate_limit_delay)
    
    def search_repositories(
        self,
        language: Optional[str] = None,
        min_stars: int = 1000,
        sort: str = "stars",
        limit: int = 10
    ) -> List[Repository]:
        """
        Search for popular repositories.
        
        Args:
            language: Programming language filter
            min_stars: Minimum number of stars
            sort: Sort order (stars, forks, updated)
            limit: Maximum number of repositories to return
            
        Returns:
            List of Repository objects
        """
        query_parts = [f"stars:>={min_stars}"]
        if language:
            query_parts.append(f"language:{language}")
        
        query = " ".join(query_parts)
        console.print(f"[cyan]Searching GitHub: {query}[/cyan]")
        
        repos = self.github.search_repositories(query, sort=sort)
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Fetching repositories...", total=None)
            
            for i, repo in enumerate(repos):
                if i >= limit:
                    break
                results.append(repo)
                self._rate_limit_delay()
                progress.update(task, description=f"Found {len(results)} repositories...")
        
        console.print(f"[green]Found {len(results)} repositories[/green]")
        return results
    
    def get_repository(self, repo_name: str) -> Repository:
        """
        Get a specific repository by name.
        
        Args:
            repo_name: Repository name in format "owner/repo"
            
        Returns:
            Repository object
        """
        self._rate_limit_delay()
        return self.github.get_repo(repo_name)
    
    def fetch_issues(
        self,
        repo: Repository,
        labels: List[str],
        state: str = "open",
        min_reactions: int = 0,
        min_comments: int = 0,
        max_issues: int = 50
    ) -> List[GitHubIssue]:
        """
        Fetch issues from a repository.
        
        Args:
            repo: Repository object
            labels: List of label names to filter by
            state: Issue state (open, closed, all)
            min_reactions: Minimum number of reactions
            min_comments: Minimum number of comments
            max_issues: Maximum number of issues to fetch
            
        Returns:
            List of GitHubIssue objects
        """
        console.print(f"[cyan]Fetching issues from {repo.full_name}...[/cyan]")
        
        # Build label filter
        label_filter = " ".join([f"label:{label}" for label in labels])
        query = f"repo:{repo.full_name} state:{state} {label_filter}"
        
        issues = self.github.search_issues(query)
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Processing issues...", total=None)
            
            for issue in issues:
                if len(results) >= max_issues:
                    break
                
                # Filter by engagement metrics
                reactions_count = issue.reactions.total_count if issue.reactions else 0
                comments_count = issue.comments
                
                if reactions_count < min_reactions or comments_count < min_comments:
                    continue
                
                # Extract labels
                issue_labels = [label.name for label in issue.labels]
                
                # Create GitHubIssue model
                github_issue = GitHubIssue(
                    repo=repo.name,
                    repo_full_name=repo.full_name,
                    issue_number=issue.number,
                    title=issue.title,
                    body=issue.body or "",
                    url=issue.html_url,
                    labels=issue_labels,
                    reactions=reactions_count,
                    comments=comments_count,
                    created_at=issue.created_at,
                    updated_at=issue.updated_at,
                    state=issue.state,
                    author=issue.user.login if issue.user else ""
                )
                
                results.append(github_issue)
                self._rate_limit_delay()
                progress.update(task, description=f"Found {len(results)} issues...")
        
        console.print(f"[green]Found {len(results)} issues from {repo.full_name}[/green]")
        return results
    
    def fetch_issues_from_repos(
        self,
        repo_names: List[str],
        labels: List[str],
        state: str = "open",
        min_reactions: int = 0,
        min_comments: int = 0,
        max_issues_per_repo: int = 50
    ) -> List[GitHubIssue]:
        """
        Fetch issues from multiple repositories.
        
        Args:
            repo_names: List of repository names (format: "owner/repo")
            labels: List of label names to filter by
            state: Issue state
            min_reactions: Minimum reactions
            min_comments: Minimum comments
            max_issues_per_repo: Max issues per repository
            
        Returns:
            List of GitHubIssue objects
        """
        all_issues = []
        
        for repo_name in repo_names:
            try:
                repo = self.get_repository(repo_name)
                issues = self.fetch_issues(
                    repo=repo,
                    labels=labels,
                    state=state,
                    min_reactions=min_reactions,
                    min_comments=min_comments,
                    max_issues=max_issues_per_repo
                )
                all_issues.extend(issues)
            except Exception as e:
                console.print(f"[red]Error fetching {repo_name}: {e}[/red]")
                continue
        
        return all_issues

