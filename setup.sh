#!/usr/bin/env bash
# Setup and build script for SimpleWish

set -e

# Parse command line arguments
BUILD_MODE=false

# Auto-detect Cloudflare Pages environment and set ROOT_DOMAIN accordingly
# Cloudflare Pages provides CF_PAGES_URL which contains the deployment URL
if [ -n "$CF_PAGES_URL" ]; then
    # Running in Cloudflare Pages build environment
    ROOT_DOMAIN="${ROOT_DOMAIN:-$CF_PAGES_URL}"
elif [ -n "$CF_PAGES_BRANCH" ]; then
    # Alternative: If CF_PAGES_BRANCH is set but CF_PAGES_URL isn't,
    # we're likely in Cloudflare but URL might be in a different variable
    ROOT_DOMAIN="${ROOT_DOMAIN:-INSERT-DOMAIN-NAME}"
else
    # Not in Cloudflare Pages environment
    ROOT_DOMAIN="${ROOT_DOMAIN:-INSERT-DOMAIN-NAME}"
fi

RECIPIENTS_DIR="${RECIPIENTS_DIR:-recipients}"
QR_OUT_DIR="${QR_OUT_DIR:-scripts/generated_qr}"
PUBLIC_DIR="${PUBLIC_DIR:-public}"

while [[ $# -gt 0 ]]; do
    case $1 in
        --build)
            BUILD_MODE=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./setup.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --build       Run Cloudflare Pages build (generate HTML, QR codes, prepare public/)"
            echo "  --help, -h    Show this help message"
            echo ""
            echo "Environment variables for --build mode:"
            echo "  ROOT_DOMAIN      Domain for QR codes"
            echo "                   Auto-detected from CF_PAGES_URL when running in Cloudflare Pages"
            echo "                   Falls back to INSERT-DOMAIN-NAME if not set"
            echo "  RECIPIENTS_DIR   Directory with recipient JSON files (default: recipients)"
            echo "  QR_OUT_DIR       Output directory for QR SVGs (default: scripts/generated_qr)"
            echo "  PUBLIC_DIR       Output directory for deployment (default: public)"
            echo ""
            echo "Cloudflare Pages:"
            echo "  When running in Cloudflare Pages, CF_PAGES_URL is automatically used as ROOT_DOMAIN"
            echo "  You can override this by explicitly setting ROOT_DOMAIN environment variable"
            echo ""
            echo "Examples:"
            echo "  ./setup.sh                                    # Normal setup"
            echo "  ./setup.sh --build                            # Build (uses CF_PAGES_URL if available)"
            echo "  ROOT_DOMAIN=\"https://example.com\" ./setup.sh --build  # Build with custom domain"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

if [ "$BUILD_MODE" = true ]; then
    echo "🎄 SimpleWish - Cloudflare Pages Build"
    echo "========================================"
    echo ""
    if [ -n "$CF_PAGES_URL" ]; then
        echo "✓ Detected Cloudflare Pages environment"
        echo "  Using CF_PAGES_URL: $CF_PAGES_URL"
        echo ""
    fi
    echo "Configuration:"
    echo "  ROOT_DOMAIN: $ROOT_DOMAIN"
    echo "  RECIPIENTS_DIR: $RECIPIENTS_DIR"
    echo "  QR_OUT_DIR: $QR_OUT_DIR"
    echo "  PUBLIC_DIR: $PUBLIC_DIR"
    echo ""
else
    echo "🎄 SimpleWish Quick Setup"
    echo "========================="
    echo ""
fi

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
if [ "$BUILD_MODE" = true ]; then
    echo "Step 1/5: Installing dependencies..."
else
    echo "Installing dependencies..."
fi
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r scripts/requirements.txt
if [ "$BUILD_MODE" = false ]; then
    pip install -q -r scripts/requirements-dev.txt
fi
echo "✓ Dependencies installed"
echo ""

if [ "$BUILD_MODE" = true ]; then
    # Build mode: Generate HTML, QR codes, and prepare for deployment
    
    # Step 2: Generate HTML for all JSON recipients
    echo "Step 2/5: Generating HTML files from recipient data..."
    if [ -d "$RECIPIENTS_DIR" ] && compgen -G "$RECIPIENTS_DIR/*.json" > /dev/null; then
        python3 scripts/generate_recipient.py --bulk --recipients-dir "$RECIPIENTS_DIR"
        echo "✓ HTML files generated"
    else
        echo "ℹ No recipient JSON files found in $RECIPIENTS_DIR, skipping generation"
    fi
    echo ""
    
    # Step 3: Generate QR SVGs
    echo "Step 3/5: Generating QR codes..."
    python3 scripts/generate_qr_svg.py --pattern "*.html" --out-dir "$QR_OUT_DIR" --root-domain "$ROOT_DOMAIN"
    echo "✓ QR codes generated"
    echo ""
    
    # Step 4: Inject generated SVGs into HTML files
    echo "Step 4/5: Injecting QR codes into HTML files..."
    python3 scripts/inject_qr_svg.py --svg-dir "$QR_OUT_DIR" --pattern "*.html"
    echo "✓ QR codes injected"
    echo ""
    
    # Step 5: Prepare public directory
    echo "Step 5/5: Preparing output directory..."
    mkdir -p "$PUBLIC_DIR"
    # Move HTML files if they exist
    if compgen -G "*.html" > /dev/null; then
        mv -- *.html "$PUBLIC_DIR/"
        echo "✓ Files moved to $PUBLIC_DIR/"
    else
        echo "⚠ No HTML files found to move"
    fi
    echo ""
    
    echo "🎉 Build complete!"
    echo ""
    echo "Output directory: $PUBLIC_DIR"
    echo "Ready for Cloudflare Pages deployment"
else
    # Setup mode: Run tests and linter
    
    # Run tests to verify everything works
    echo "Running tests to verify setup..."
    python3 -m pytest -q
    echo "✓ Tests passed"
    echo ""
    
    # Run linter
    echo "Running linter..."
    python3 -m flake8
    echo "✓ Linter passed"
    echo ""
    
    echo "🎉 Setup complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Copy index.html to create a new list (e.g., alice.html)"
    echo "  2. Edit the HTML file with gift ideas"
    echo "  3. Generate QR codes:"
    echo "     python3 scripts/generate_qr_svg.py --root-domain YOUR_GITHUB_PAGES_URL --pattern '*.html' --out-dir scripts/generated_qr"
    echo "  4. Inject QR codes into HTML files:"
    echo "     python3 scripts/inject_qr_svg.py --svg-dir scripts/generated_qr --pattern '*.html'"
    echo ""
    echo "See README.md for more details!"
fi
