#!/usr/bin/env bash
# Quick setup script for SimpleWish

set -e

echo "🎄 SimpleWish Quick Setup"
echo "========================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "   Please install Python 3.11 or later"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Found Python $PYTHON_VERSION"
echo ""

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment and install dependencies
echo "Installing dependencies..."
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r scripts/requirements.txt
pip install -q -r scripts/requirements-dev.txt
echo "✓ Dependencies installed"
echo ""

# Run tests to verify everything works
echo "Running tests to verify setup..."
python -m pytest -q
echo "✓ Tests passed"
echo ""

# Run linter
echo "Running linter..."
flake8
echo "✓ Linter passed"
echo ""

echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Copy index.html to create a new list (e.g., alice.html)"
echo "  2. Edit the HTML file with gift ideas"
echo "  3. Generate QR codes:"
echo "     python scripts/generate_qr_svg.py --root-domain YOUR_GITHUB_PAGES_URL --pattern '*.html' --out-dir scripts/generated_qr"
echo "  4. Inject QR codes into HTML files:"
echo "     python scripts/inject_qr_svg.py --svg-dir scripts/generated_qr --pattern '*.html'"
echo ""
echo "See README.md for more details!"
