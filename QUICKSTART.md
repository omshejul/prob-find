# Quick Start Guide

## 1. Setup (One-time)

```bash
# Run the setup script
./setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configure API Keys

Edit `.env` file:

```bash
GEMINI_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here  # Optional but recommended
```

Get your keys:

- Gemini: https://aistudio.google.com/apikey
- GitHub: https://github.com/settings/tokens

## 3. Check Configuration

```bash
python main.py check
```

## 4. Run the Scraper

### Basic usage:

```bash
python main.py run
```

### Advanced examples:

```bash
# Search Python repos with 10k+ stars
python main.py run --language python --min-stars 10000

# Analyze specific repositories
python main.py run --repos "facebook/react,vercel/next.js"

# Filter by labels
python main.py run --labels "help-wanted,good-first-issue"
```

## 5. View Results

Results are saved to `output/`:

- `opportunities.json` - Full data
- `opportunities.csv` - Spreadsheet format

## Troubleshooting

**"GEMINI_API_KEY not set"**

- Make sure `.env` file exists and has your API key

**"No opportunities found"**

- Lower `min_opportunity_score` in `config.yaml`
- Check that repos have open issues with specified labels

**Rate limit errors**

- Wait a few minutes and try again
- Reduce `max_issues_per_repo` in `config.yaml`
