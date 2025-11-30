#!/bin/bash
# Setup script for GitHub Opportunity Scraper

set -e

echo "🚀 Setting up GitHub Opportunity Scraper..."
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Create .env file from .env.example if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📝 Creating .env file from .env.example..."
        cp .env.example .env
        echo "✓ .env file created"
    else
        echo "📝 Creating .env file..."
        cat > .env << EOF
# GitHub API Token (optional but recommended for higher rate limits)
# Get one at: https://github.com/settings/tokens
GITHUB_TOKEN=

# Google Gemini API Key (required)
# Get one at: https://aistudio.google.com/apikey
GEMINI_API_KEY=
EOF
        echo "✓ .env file created"
    fi
    echo ""
    echo "⚠️  Please edit .env and add your GEMINI_API_KEY"
    echo "   Get your key at: https://aistudio.google.com/apikey"
else
    echo "✓ .env file already exists"
fi

# Create output directory
mkdir -p output
echo "✓ Output directory created"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your GEMINI_API_KEY"
echo "2. (Optional) Add GITHUB_TOKEN for higher rate limits"
echo "3. Run: python main.py check"
echo "4. Run: python main.py run"

