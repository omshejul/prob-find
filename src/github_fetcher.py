"""GitHub API integration for fetching repositories and issues."""

import os
import json
import time
from pathlib import Path
from typing import List, Optional, Set
from github import Github
from github.Repository import Repository
from github.GithubException import GithubException
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .models import GitHubIssue
from .exceptions import GitHubRateLimitExceeded

console = Console()


class GitHubFetcher:
    """Fetches repositories and issues from GitHub API."""

    EXCLUDED_REPO_KEYWORDS = [
        "awesome",
        "course",
        "courses",
        "bootcamp",
        "boot camp",
        "curriculum",
        "tutorial",
        "tutorials",
        "tutorial-code",
        "docs",
        "documentation",
        "guide",
        "guides",
        "handbook",
        "roadmap",
        "roadmaps",
        "learning",
        "learn-",
        "learn ",
        "interview",
        "coding-interview",
        "coding interview",
        "cheatsheet",
        "cheat-sheet",
        "book",
        "Microsoft-Activation-Scripts",
        "bootstrap",
        "books",
        "ebook",
        "ebooks",
        "syllabus",
        "boot.dev",
        "codecrafters",
        "freecodecamp",
        "system-design-primer",
        "free-programming",
        "developer-roadmap",
    ]
    
    def __init__(
        self,
        token: Optional[str] = None,
        rate_limit_delay: float = 0.1,
        cache_file: Optional[str] = None
    ):
        """
        Initialize GitHub fetcher.
        
        Args:
            token: GitHub personal access token (optional but recommended)
            rate_limit_delay: Delay between requests in seconds
            cache_file: Path to JSON file storing searched repositories cache
        """
        self.github = Github(token) if token else Github()
        self.rate_limit_delay = rate_limit_delay
        self.cache_file = cache_file or "output/searched_repos.json"
        self.searched_repos: Set[str] = self._load_cache()
        self._check_rate_limit()

    def _handle_github_exception(self, error: GithubException) -> None:
        """Convert GitHub exceptions into scraper-friendly errors."""
        message = ""

        if hasattr(error, "data") and isinstance(error.data, dict):
            message = error.data.get("message", "") or ""
        elif error.args:
            message = str(error.args[0])

        message_lower = message.lower()
        status = getattr(error, "status", None)

        if (
            (status in {403, 429})
            or "rate limit" in message_lower
            or "abuse detection" in message_lower
        ):
            raise GitHubRateLimitExceeded(message or "GitHub API rate limit exceeded") from error

        raise error
    
    def _check_rate_limit(self) -> None:
        """Check and display current rate limit status."""
        try:
            rate_limit = self.github.get_rate_limit()
        except GithubException as exc:
            self._handle_github_exception(exc)
            return

        # PyGithub <2.2 exposed .core; newer versions expose .rate
        core_rate = getattr(rate_limit, "core", None) or getattr(rate_limit, "rate", None)

        # Fallback to resources dict if available
        if core_rate is None and hasattr(rate_limit, "resources"):
            core_rate = rate_limit.resources.get("core")

        if core_rate is None:
            console.print("[yellow]Warning: Unable to read GitHub rate limit information (API response changed?). Continuing...[/yellow]")
            return

        remaining = getattr(core_rate, "remaining", None)
        reset_time = getattr(core_rate, "reset", None)

        if remaining is None:
            console.print("[yellow]Warning: GitHub rate limit remaining value unavailable.[/yellow]")
            return
        
        reset_display = reset_time if reset_time is not None else "unknown"
        
        if remaining < 100:
            console.print(f"[yellow]Warning: Only {remaining} GitHub API requests remaining. Resets at {reset_display}[/yellow]")
        else:
            console.print(f"[green]GitHub API: {remaining} requests remaining[/green]")
    
    def _rate_limit_delay(self) -> None:
        """Apply rate limiting delay."""
        if self.rate_limit_delay > 0:
            time.sleep(self.rate_limit_delay)
    
    def _load_cache(self) -> Set[str]:
        """Load searched repositories from cache file."""
        cache_path = Path(self.cache_file)
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    repos = data.get("repositories", [])
                    return set(repos)
            except (json.JSONDecodeError, IOError) as e:
                console.print(f"[yellow]Warning: Could not load cache file: {e}[/yellow]")
        return set()
    
    def _save_cache(self) -> None:
        """Save searched repositories to cache file."""
        cache_path = Path(self.cache_file)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "repositories": sorted(list(self.searched_repos)),
                        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
                    },
                    f,
                    indent=2
                )
        except IOError as e:
            console.print(f"[yellow]Warning: Could not save cache file: {e}[/yellow]")
    
    def _mark_repo_searched(self, repo_full_name: str) -> None:
        """Mark a repository as searched and save to cache."""
        self.searched_repos.add(repo_full_name)
        self._save_cache()
    
    def is_repo_searched(self, repo_full_name: str) -> bool:
        """Check if a repository has already been searched."""
        return repo_full_name in self.searched_repos

    def _is_tool_repository(self, repo: Repository) -> bool:
        """
        Heuristically determine if a repository is a product/tool rather than documentation courses, or curated lists.
        """
        text = f"{repo.full_name} {(repo.description or '')}".lower()

        for keyword in self.EXCLUDED_REPO_KEYWORDS:
            if keyword in text:
                return False

        if getattr(repo, "archived", False):
            return False

        return True
    
    def search_repositories(
        self,
        language: Optional[str] = None,
        min_stars: int = 1000,
        sort: str = "stars",
        limit: int = 100
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
        
        try:
            repos = self.github.search_repositories(query, sort=sort)
        except GithubException as exc:
            self._handle_github_exception(exc)
            return []
        results = []
        skipped = 0
        already_searched = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Fetching repositories...", total=None)
            
            try:
                for repo in repos:
                    if len(results) >= limit:
                        break

                    # Skip if already searched
                    if self.is_repo_searched(repo.full_name):
                        already_searched += 1
                        continue

                    if not self._is_tool_repository(repo):
                        skipped += 1
                        progress.update(task, description=f"Skipped {skipped} non-tool repos...")
                        continue

                    results.append(repo)
                    self._rate_limit_delay()
                    progress.update(task, description=f"Selected {len(results)} tool repos...")
            except GithubException as exc:
                self._handle_github_exception(exc)
        
        if already_searched > 0:
            console.print(f"[cyan]Skipped {already_searched} repositories already searched (cached)[/cyan]")
        if skipped:
            console.print(f"[yellow]Skipped {skipped} repositories that looked like documentation/courses/lists[/yellow]")

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
        try:
            return self.github.get_repo(repo_name)
        except GithubException as exc:
            self._handle_github_exception(exc)
    
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
        
        label_list = labels or [None]
        results: List[GitHubIssue] = []
        seen_keys = set()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Processing issues...", total=None)

            for label in label_list:
                if len(results) >= max_issues:
                    break

                query_parts = [
                    f"repo:{repo.full_name}",
                    "is:issue",
                    f"state:{state}",
                ]

                if label:
                    query_parts.append(f"label:{label}")

                query = " ".join(query_parts)

                try:
                    issues = self.github.search_issues(query)
                except GithubException as exc:
                    self._handle_github_exception(exc)
                    return results

                try:
                    for issue in issues:
                        if len(results) >= max_issues:
                            break

                        issue_key = (issue.number, issue.repository.full_name if hasattr(issue, "repository") else repo.full_name)
                        if issue_key in seen_keys:
                            continue

                        # Filter by engagement metrics
                        reactions = getattr(issue, "reactions", None)
                        if isinstance(reactions, dict):
                            reactions_count = reactions.get("total_count", 0)
                        elif reactions is not None and hasattr(reactions, "total_count"):
                            reactions_count = reactions.total_count
                        else:
                            reactions_count = 0
                        comments_count = issue.comments
                        
                        if reactions_count < min_reactions or comments_count < min_comments:
                            continue
                        
                        # Extract labels
                        issue_labels = [label_obj.name for label_obj in issue.labels]
                        
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
                        seen_keys.add(issue_key)
                        self._rate_limit_delay()
                        progress.update(task, description=f"Found {len(results)} issues...")
                except GithubException as exc:
                    self._handle_github_exception(exc)
                    return results
        
        console.print(f"[green]Found {len(results)} issues from {repo.full_name}[/green]")
        # Mark repository as searched after fetching issues
        self._mark_repo_searched(repo.full_name)
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
                # Skip if already searched
                if self.is_repo_searched(repo_name):
                    console.print(f"[cyan]Skipping {repo_name} (already searched)[/cyan]")
                    continue
                
                repo = self.get_repository(repo_name)
                if not self._is_tool_repository(repo):
                    console.print(f"[yellow]Skipping {repo_name} (looks like documentation/course/list repository)[/yellow]")
                    continue
                issues = self.fetch_issues(
                    repo=repo,
                    labels=labels,
                    state=state,
                    min_reactions=min_reactions,
                    min_comments=min_comments,
                    max_issues=max_issues_per_repo
                )
                all_issues.extend(issues)
            except GitHubRateLimitExceeded:
                raise
            except Exception as e:
                console.print(f"[red]Error fetching {repo_name}: {e}[/red]")
                continue
        
        return all_issues

