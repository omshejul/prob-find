# GitHub Opportunity Scraper

A Python tool to scrape GitHub issues and feature requests from popular open source projects, then use Google Gemini AI to analyze them and identify potential business opportunities.

## Features

- 🔍 **Smart Repository Discovery**: Search GitHub by language, stars, or specify repositories directly
- 📊 **Issue Filtering**: Filter by labels, engagement metrics (reactions, comments)
- 🤖 **AI-Powered Analysis**: Uses Gemini 2.5 Flash to score opportunities on:
  - Market Potential (1-10)
  - Technical Feasibility (1-10)
  - Competition (1-10)
  - Monetization Fit (1-10)
- 📁 **Multiple Output Formats**: Export to JSON and CSV
- ⚡ **Rate Limiting**: Built-in rate limiting for both GitHub and Gemini APIs

## Prerequisites

- Python 3.8+
- GitHub API token (optional but recommended)
- Google Gemini API key (required)

## Installation

1. **Clone or navigate to the project directory:**

   ```bash
   cd prob-find
   ```

2. **Create and activate virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**

   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

   Get your API keys:

   - **GitHub Token**: https://github.com/settings/tokens (optional, but recommended)
   - **Gemini API Key**: https://aistudio.google.com/apikey (required)

## Configuration

Edit `config.yaml` to customize:

- Target repositories or search criteria
- Issue labels to filter
- Minimum engagement thresholds
- AI model settings
- Output preferences

## Usage

### Basic Usage

```bash
# Run with default config
python main.py run

# Check configuration
python main.py check
```

### Advanced Usage

```bash
# Specify repositories directly
python main.py run --repos "facebook/react,vercel/next.js"

# Search by language and minimum stars
python main.py run --language python --min-stars 10000

# Filter by specific labels
python main.py run --labels "help-wanted,good-first-issue"

# Use custom config file
python main.py run --config my-config.yaml
```

## Output

Results are saved to the `output/` directory:

- **`opportunities.json`**: Full structured data with all metadata
- **`opportunities.csv`**: Spreadsheet-friendly format for analysis

Each opportunity includes:

- Repository and issue details
- Engagement metrics (reactions, comments)
- AI analysis scores
- Opportunity summary and product ideas

## Rate Limits

- **GitHub API**: 5,000 requests/hour (authenticated)
- **Gemini API**: 15 requests/minute, 1M tokens/day (free tier)

The tool includes built-in rate limiting to stay within these limits.

## Project Structure

```
prob-find/
├── src/
│   ├── __init__.py
│   ├── github_fetcher.py    # GitHub API integration
│   ├── analyzer.py           # Gemini AI analysis
│   ├── output.py            # JSON/CSV output handlers
│   └── models.py            # Pydantic data models
├── config.yaml              # Configuration file
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
└── output/                  # Generated reports
```

## Example Output

```json
{
  "opportunities": [
    {
      "repo": "next.js",
      "issue_number": 12345,
      "title": "Support for X feature",
      "url": "https://github.com/vercel/next.js/issues/12345",
      "reactions": 156,
      "comments": 42,
      "ai_analysis": {
        "market_potential": 8,
        "technical_feasibility": 7,
        "competition": 5,
        "monetization_fit": 6,
        "total_score": 26,
        "opportunity_summary": "High demand feature with moderate competition...",
        "product_idea": "Standalone tool for X feature..."
      }
    }
  ]
}
```

## Troubleshooting

**"GEMINI_API_KEY not set"**

- Make sure you've created a `.env` file with your API key
- Get your key from: https://aistudio.google.com/apikey

**"Rate limit exceeded"**

- The tool includes rate limiting, but if you hit limits:
  - Wait for the reset period
  - Reduce `max_issues_per_repo` in config.yaml
  - Use GitHub token for higher limits

**"No opportunities found"**

- Try lowering `min_opportunity_score` in config.yaml
- Check that repositories have open issues with the specified labels
- Verify your search criteria aren't too restrictive

## License

MIT

## Contributing

This is a personal tool, but feel free to fork and adapt for your needs!
