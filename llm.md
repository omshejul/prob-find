# Project Function Documentation

### `src/models.py::model_post_init`

**Signature:** `def model_post_init(self, __context) -> None`

**Description:** Calculate total_score after initialization.

**Parameters:**

- `self`: Any
- `__context`: Any

**Returns:** `None`

---

### `src/analyzer.py::__init__`

**Signature:** `def __init__(self, api_key: str, model: str, fallback_model: str, temperature: float, requests_per_minute: int)`

**Description:** Initialize the analyzer.

Args:
api_key: Google Gemini API key
model: Primary model to use
fallback_model: Fallback model if primary fails
temperature: Model temperature (0.0-1.0)
requests_per_minute: Rate limit (default 12 to stay under 15 RPM free tier)

**Parameters:**

- `self`: Any
- `api_key`: str
- `model`: str
- `fallback_model`: str
- `temperature`: float
- `requests_per_minute`: int

**Returns:** `None`

---

### `src/analyzer.py::_is_rate_limit_error`

**Signature:** `def _is_rate_limit_error(error: Exception) -> bool`

**Description:** Determine whether the provided error is a Gemini rate limit error.

**Parameters:**

- `error`: Exception

**Returns:** `bool`

---

### `src/analyzer.py::_rate_limit`

**Signature:** `def _rate_limit(self) -> None`

**Description:** Enforce rate limiting.

**Parameters:**

- `self`: Any

**Returns:** `None`

---

### `src/analyzer.py::_create_prompt`

**Signature:** `def _create_prompt(self, issue: GitHubIssue) -> str`

**Description:** Create analysis prompt from GitHub issue.

**Parameters:**

- `self`: Any
- `issue`: GitHubIssue

**Returns:** `str`

---

### `src/analyzer.py::_ensure_total_score`

**Signature:** `def _ensure_total_score(analysis: OpportunityAnalysis) -> OpportunityAnalysis`

**Description:** Ensure total_score is populated even if the model omits it. Only recalculates if total_score is None or not an integer. Note: total == 0 is impossible since all scores have ge=1 constraint (min total = 4).

**Parameters:**

- `analysis`: OpportunityAnalysis

**Returns:** `OpportunityAnalysis`

---

### `src/analyzer.py::analyze_issue`

**Signature:** `def analyze_issue(self, issue: GitHubIssue) -> Optional[OpportunityAnalysis]`

**Description:** Analyze a single GitHub issue.

Args:
issue: GitHubIssue to analyze

Returns:
OpportunityAnalysis or None if analysis fails

**Parameters:**

- `self`: Any
- `issue`: GitHubIssue

**Returns:** `Optional[OpportunityAnalysis]`

---

### `src/analyzer.py::analyze_issues`

**Signature:** `def analyze_issues(self, issues: List[GitHubIssue], min_score: int, show_progress: bool) -> List[OpportunityAnalysis]`

**Description:** Analyze multiple issues and return only high-scoring opportunities.

Args:
issues: List of GitHubIssue objects
min_score: Minimum total score to include
show_progress: Whether to show progress bar

Returns:
List of OpportunityAnalysis objects with score >= min_score

**Parameters:**

- `self`: Any
- `issues`: List[GitHubIssue]
- `min_score`: int
- `show_progress`: bool

**Returns:** `List[OpportunityAnalysis]`

---

### `src/output.py::__init__`

**Signature:** `def __init__(self, output_dir: str)`

**Description:** Initialize output writer.

Args:
output_dir: Directory to write output files

**Parameters:**

- `self`: Any
- `output_dir`: str

**Returns:** `None`

---

### `src/output.py::_opportunity_to_dict`

**Signature:** `def _opportunity_to_dict(self, issue: GitHubIssue, analysis: OpportunityAnalysis) -> dict`

**Description:** Convert issue and analysis to dictionary.

**Parameters:**

- `self`: Any
- `issue`: GitHubIssue
- `analysis`: OpportunityAnalysis

**Returns:** `dict`

---

### `src/output.py::write_json`

**Signature:** `def write_json(self, issues: List[GitHubIssue], analyses: List[OpportunityAnalysis], filename: str, sort_by: str) -> None`

**Description:** Write opportunities to JSON file.

Args:
issues: List of GitHubIssue objects
analyses: List of OpportunityAnalysis objects (must match issues)
filename: Output filename
sort_by: Field to sort by (default: total_score)

**Parameters:**

- `self`: Any
- `issues`: List[GitHubIssue]
- `analyses`: List[OpportunityAnalysis]
- `filename`: str
- `sort_by`: str

**Returns:** `None`

---

### `src/output.py::write_csv`

**Signature:** `def write_csv(self, issues: List[GitHubIssue], analyses: List[OpportunityAnalysis], filename: str, sort_by: str) -> None`

**Description:** Write opportunities to CSV file.

Args:
issues: List of GitHubIssue objects
analyses: List of OpportunityAnalysis objects (must match issues)
filename: Output filename
sort_by: Field to sort by (default: total_score)

**Parameters:**

- `self`: Any
- `issues`: List[GitHubIssue]
- `analyses`: List[OpportunityAnalysis]
- `filename`: str
- `sort_by`: str

**Returns:** `None`

---

### `src/github_fetcher.py::__init__`

**Signature:** `def __init__(self, token: Optional[str], rate_limit_delay: float, cache_file: Optional[str])`

**Description:** Initialize GitHub fetcher.

Args:
token: GitHub personal access token (optional but recommended)
rate_limit_delay: Delay between requests in seconds
cache_file: Path to JSON file storing searched repositories cache

**Parameters:**

- `self`: Any
- `token`: Optional[str]
- `rate_limit_delay`: float
- `cache_file`: Optional[str]

**Returns:** `None`

---

### `src/github_fetcher.py::_handle_github_exception`

**Signature:** `def _handle_github_exception(self, error: GithubException) -> None`

**Description:** Convert GitHub exceptions into scraper-friendly errors.

**Parameters:**

- `self`: Any
- `error`: GithubException

**Returns:** `None`

---

### `src/github_fetcher.py::_check_rate_limit`

**Signature:** `def _check_rate_limit(self) -> None`

**Description:** Check and display current rate limit status.

**Parameters:**

- `self`: Any

**Returns:** `None`

---

### `src/github_fetcher.py::_rate_limit_delay`

**Signature:** `def _rate_limit_delay(self) -> None`

**Description:** Apply rate limiting delay.

**Parameters:**

- `self`: Any

**Returns:** `None`

---

### `src/github_fetcher.py::_load_cache`

**Signature:** `def _load_cache(self) -> Set[str]`

**Description:** Load searched repositories from cache file.

**Parameters:**

- `self`: Any

**Returns:** `Set[str]`

---

### `src/github_fetcher.py::_save_cache`

**Signature:** `def _save_cache(self) -> None`

**Description:** Save searched repositories to cache file.

**Parameters:**

- `self`: Any

**Returns:** `None`

---

### `src/github_fetcher.py::_mark_repo_searched`

**Signature:** `def _mark_repo_searched(self, repo_full_name: str) -> None`

**Description:** Mark a repository as searched and save to cache.

**Parameters:**

- `self`: Any
- `repo_full_name`: str

**Returns:** `None`

---

### `src/github_fetcher.py::is_repo_searched`

**Signature:** `def is_repo_searched(self, repo_full_name: str) -> bool`

**Description:** Check if a repository has already been searched.

**Parameters:**

- `self`: Any
- `repo_full_name`: str

**Returns:** `bool`

---

### `src/github_fetcher.py::_is_tool_repository`

**Signature:** `def _is_tool_repository(self, repo: Repository) -> bool`

**Description:** Heuristically determine if a repository is a product/tool rather than documentation courses, or curated lists.

**Parameters:**

- `self`: Any
- `repo`: Repository

**Returns:** `bool`

---

### `src/github_fetcher.py::search_repositories`

**Signature:** `def search_repositories(self, language: Optional[str], min_stars: int, sort: str, limit: int) -> List[Repository]`

**Description:** Search for popular repositories.

Args:
language: Programming language filter
min_stars: Minimum number of stars
sort: Sort order (stars, forks, updated)
limit: Maximum number of repositories to return

Returns:
List of Repository objects

**Parameters:**

- `self`: Any
- `language`: Optional[str]
- `min_stars`: int
- `sort`: str
- `limit`: int

**Returns:** `List[Repository]`

---

### `src/github_fetcher.py::get_repository`

**Signature:** `def get_repository(self, repo_name: str) -> Repository`

**Description:** Get a specific repository by name.

Args:
repo_name: Repository name in format "owner/repo"

Returns:
Repository object

**Parameters:**

- `self`: Any
- `repo_name`: str

**Returns:** `Repository`

---

### `src/github_fetcher.py::fetch_issues`

**Signature:** `def fetch_issues(self, repo: Repository, labels: List[str], state: str, min_reactions: int, min_comments: int, max_issues: int) -> List[GitHubIssue]`

**Description:** Fetch issues from a repository.

Args:
repo: Repository object
labels: List of label names to filter by
state: Issue state (open, closed, all)
min_reactions: Minimum number of reactions
min_comments: Minimum number of comments
max_issues: Maximum number of issues to fetch

Returns:
List of GitHubIssue objects

**Parameters:**

- `self`: Any
- `repo`: Repository
- `labels`: List[str]
- `state`: str
- `min_reactions`: int
- `min_comments`: int
- `max_issues`: int

**Returns:** `List[GitHubIssue]`

---

### `src/github_fetcher.py::fetch_issues_from_repos`

**Signature:** `def fetch_issues_from_repos(self, repo_names: List[str], labels: List[str], state: str, min_reactions: int, min_comments: int, max_issues_per_repo: int) -> List[GitHubIssue]`

**Description:** Fetch issues from multiple repositories.

Args:
repo_names: List of repository names (format: "owner/repo")
labels: List of label names to filter by
state: Issue state
min_reactions: Minimum reactions
min_comments: Minimum comments
max_issues_per_repo: Max issues per repository

Returns:
List of GitHubIssue objects

**Parameters:**

- `self`: Any
- `repo_names`: List[str]
- `labels`: List[str]
- `state`: str
- `min_reactions`: int
- `min_comments`: int
- `max_issues_per_repo`: int

**Returns:** `List[GitHubIssue]`
