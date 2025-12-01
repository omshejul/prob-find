"""Custom exceptions for the GitHub Opportunity Scraper."""


class GitHubRateLimitExceeded(Exception):
    """Raised when the GitHub API rate limit has been exceeded."""


class GeminiRateLimitExceeded(Exception):
    """Raised when the Gemini API rate limit has been exceeded."""
