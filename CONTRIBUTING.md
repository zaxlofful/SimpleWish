# Contributing to SimpleWish

Thank you for your interest in contributing! This is a small, focused project for creating printable Christmas gift lists.

## Quick Start

1. **Fork and clone** the repository
2. **Create a branch** from `main`
3. **Make your changes** (keep them small and focused)
4. **Run tests and linting** locally before submitting
5. **Open a PR** with a clear description

## Development Setup

### Prerequisites
- Python 3.11+
- pip

### Installation

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r scripts/requirements.txt
pip install -r scripts/requirements-dev.txt
```

### Running Tests

```bash
# Run all tests
python3 -m pytest -v

# Run linter
python3 -m flake8
```

### Testing QR Generation

```bash
# Generate QR SVGs
python3 scripts/generate_qr_svg.py --root-domain "https://example.com" --pattern "*.html" --out-dir scripts/generated_qr

# Inject QR SVGs into HTML files
python3 scripts/inject_qr_svg.py --svg-dir scripts/generated_qr --pattern "*.html"
```

## Guidelines

### Code Style
- Follow PEP 8 (enforced by flake8)
- Keep functions small and focused
- Add docstrings for non-trivial functions

### HTML/CSS
- Maintain the **single-file guarantee**: All styles inline, QR codes embedded
- Preserve print-friendly layout
- Test on multiple browsers if changing CSS
- Ensure accessibility (semantic HTML, proper contrast)

### Commits
- Use clear, descriptive commit messages
- Keep commits focused on a single change
- Reference issues when applicable

### Pull Requests
- Describe what changes you made and why
- Include screenshots for UI changes
- Link to relevant issues
- Ensure CI checks pass

## Areas for Contribution

- 🎨 New color themes or design variations
- 📝 Documentation improvements
- 🧪 Additional test coverage
- 🐛 Bug fixes
- ✨ New features (discuss in an issue first for larger changes)

## Questions?

Open an issue or start a discussion. We're happy to help!

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
