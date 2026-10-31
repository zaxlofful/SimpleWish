#!/usr/bin/env bash

set -euo pipefail

BUILD_MODE=false
if [[ -n "${CF_PAGES_URL:-}" ]]; then
    ROOT_DOMAIN="${ROOT_DOMAIN:-$CF_PAGES_URL}"
else
    ROOT_DOMAIN="${ROOT_DOMAIN:-INSERT-DOMAIN-NAME}"
fi

RECIPIENTS_DIR="${RECIPIENTS_DIR:-recipients}"
QR_OUT_DIR="${QR_OUT_DIR:-scripts/generated_qr}"
PUBLIC_DIR="${PUBLIC_DIR:-public}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --build)
            BUILD_MODE=true
            shift
            ;;
        --help|-h)
            cat <<'EOF'
Usage: ./setup.sh [OPTIONS]

Options:
  --build       Generate recipient HTML and QR codes for deployment
  --help, -h    Show this help message

Build environment:
  ROOT_DOMAIN      Public domain for QR codes
  RECIPIENTS_DIR   Recipient JSON directory (default: recipients)
  QR_OUT_DIR       Generated SVG directory (default: scripts/generated_qr)
  PUBLIC_DIR       Deployment output directory (default: public)
EOF
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

if ! command -v cargo >/dev/null 2>&1; then
    echo "Error: Rust and Cargo are required. Install the stable Rust toolchain." >&2
    exit 1
fi

echo "Found $(rustc --version)"
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all

if [[ "$BUILD_MODE" != true ]]; then
    echo "Setup complete. Run ./setup.sh --build to prepare deployment files."
    exit 0
fi

echo "Building SimpleWish for $ROOT_DOMAIN"
cargo run --release -- generate-recipient --bulk --recipients-dir "$RECIPIENTS_DIR"
cargo run --release -- generate-qr --pattern "*.html" --out-dir "$QR_OUT_DIR" --root-domain "$ROOT_DOMAIN"
cargo run --release -- inject-qr --svg-dir "$QR_OUT_DIR" --pattern "*.html"

mkdir -p "$PUBLIC_DIR"
shopt -s nullglob
html_files=( *.html )
if (( ${#html_files[@]} )); then
    mv -- "${html_files[@]}" "$PUBLIC_DIR/"
    echo "HTML files moved to $PUBLIC_DIR/"
else
    echo "No HTML files found to move"
fi
echo "Build complete. Output directory: $PUBLIC_DIR"
