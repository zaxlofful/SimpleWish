#!/usr/bin/env bash
# Cloudflare Pages build script for SimpleWish
# This script consolidates all build steps needed for Cloudflare Pages deployment

set -e

# Configuration
ROOT_DOMAIN="${ROOT_DOMAIN:-INSERT-DOMAIN-NAME}"
RECIPIENTS_DIR="${RECIPIENTS_DIR:-recipients}"
QR_OUT_DIR="${QR_OUT_DIR:-scripts/generated_qr}"
PUBLIC_DIR="${PUBLIC_DIR:-public}"

echo "🎄 SimpleWish - Cloudflare Pages Build"
echo "========================================"
echo ""
echo "Configuration:"
echo "  ROOT_DOMAIN: $ROOT_DOMAIN"
echo "  RECIPIENTS_DIR: $RECIPIENTS_DIR"
echo "  QR_OUT_DIR: $QR_OUT_DIR"
echo "  PUBLIC_DIR: $PUBLIC_DIR"
echo ""

# Step 1: Create virtual environment and install dependencies
echo "Step 1/5: Setting up Python environment..."
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r scripts/requirements.txt
echo "✓ Environment ready"
echo ""

# Step 2: Generate HTML for all JSON recipients
echo "Step 2/5: Generating HTML files from recipient data..."
if [ -d "$RECIPIENTS_DIR" ] && compgen -G "$RECIPIENTS_DIR/*.json" > /dev/null; then
    python scripts/generate_recipient.py --bulk --recipients-dir "$RECIPIENTS_DIR"
    echo "✓ HTML files generated"
else
    echo "ℹ No recipient JSON files found in $RECIPIENTS_DIR, skipping generation"
fi
echo ""

# Step 3: Generate QR SVGs
echo "Step 3/5: Generating QR codes..."
python scripts/generate_qr_svg.py --pattern "*.html" --out-dir "$QR_OUT_DIR" --root-domain "$ROOT_DOMAIN"
echo "✓ QR codes generated"
echo ""

# Step 4: Inject generated SVGs into HTML files
echo "Step 4/5: Injecting QR codes into HTML files..."
python scripts/inject_qr_svg.py --svg-dir "$QR_OUT_DIR" --pattern "*.html"
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
