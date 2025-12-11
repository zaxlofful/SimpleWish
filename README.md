[![Lint](https://github.com/ZaxLofful/SimpleWish/actions/workflows/lint.yml/badge.svg)](https://github.com/zaxlofful/SimpleWish/actions/workflows/lint.yml)
[![pytest](https://github.com/ZaxLofful/SimpleWish/actions/workflows/pytest.yml/badge.svg)](https://github.com/zaxlofful/SimpleWish/actions/workflows/pytest.yml)
[![Generate QR](https://github.com/ZaxLofful/SimpleWish/actions/workflows/generate-qrs.yml/badge.svg)](https://github.com/zaxlofful/SimpleWish/actions/workflows/generate-qrs.yml)

# SimpleWish - Christmas List Template

A printable, single-file HTML template for creating personalized Christmas gift lists.

## ✨ Features

- **Single-file design** — Each HTML file is completely self-contained (no external dependencies)
- **Printable** — Optimized layout for printing or saving as PDF
- **QR codes** — Automatically generated QR codes for easy sharing
- **Customizable** — Change colors, add your own items, personalize for each recipient
- **Cloudflare Pages ready** — Designed to work seamlessly with Cloudflare Pages and custom domains
- **CI/CD ready** — Automated QR generation workflows

## 🚀 Quick Start

### Option 1: Use as Template (Recommended)

This is the easiest way to get started. GitHub Actions will handle QR code generation automatically!

1. **Fork this repository** (or use as template)

2. **Configure your domain** (Important!):
   - Go to your repo → Settings → Secrets and variables → Actions
   - Option A (Recommended for private repos): Secrets tab → New repository secret
   - Option B (Easier for public repos): Variables tab → New repository variable
   - Name: `ROOT_DOMAIN`
   - Value: Your deployment URL (e.g., `https://yourname.github.io/SimpleWish` or `https://yourdomain.com`)
   - Note: Secrets take priority over variables if both are set
      - Note: Secrets take priority over variables if both are set. The workflow used to generate QR SVGs sets `ROOT_DOMAIN` with the following precedence: default (`https://example.com`) -> repository variable `ROOT_DOMAIN` -> secret `ROOT_DOMAIN` (secret overwrites variable).

3. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/SimpleWish.git
   cd SimpleWish
   ```

4. **Create personalized lists (recommended)**

    The project now supports generating per-recipient HTML from simple JSON files. Add one JSON file per person to the `recipients` directory. The CI build will generate HTML pages and inject QR SVGs at deploy time (generated files are not committed to the repo).

   See the included `elsa.html` file for a ready-made example.

5. **Commit and push the source (NOT generated HTML)**

    ```bash
    git add recipients/*.json
    git commit -m "Add recipient JSON files"
    git push
    ```

6. **Deploy** (choose one)

   1. **Cloudflare Pages** (Recommended):
      - Connect your repo to Cloudflare Pages through the web GUI.
      - **Build command** (paste into the Pages web GUI build command):
      
      ```bash
      ./setup.sh --build
      ```
      
      - **Output directory**: `public`
      
      The build script automatically detects Cloudflare Pages environment variables:
      - **Auto-detection**: When running in Cloudflare Pages, the script automatically uses `CF_PAGES_URL` for QR code generation
      - **Custom domain override**: You can override by setting `ROOT_DOMAIN` environment variable in Cloudflare Pages settings
      
      Example with custom domain override:
      ```bash
      ROOT_DOMAIN="https://yourcustomdomain.com" ./setup.sh --build
      ```
      
      The build command (`setup.sh --build`) automatically handles:
      - Setting up Python virtual environment
      - Installing dependencies
      - Generating HTML from recipient JSON files
      - Creating QR codes with your domain (auto-detected or custom)
      - Injecting QR codes into HTML files
      - Preparing the `public/` directory for deployment

      - **Why this matters**: Cloudflare Pages will deploy only what you put in `public/`, so generating and injecting pages in the build step keeps the repository free of generated artifacts and preserves privacy/security of scripts and configs.
   2. **GitHub Pages** (Optional):
      - Use the repository Actions workflow: go to Actions → "Deploy to GitHub Pages (Optional)" → Run workflow.
      - The workflow will generate per-recipient HTML from `recipients/*.json`, run QR generation and injection, and upload the produced `public/` folder to GitHub Pages.

**That's it!** The Cloudflare/GitHub workflows will automatically:
- Generate per-recipient HTML from `recipients/*.json` using `index.html` as the template
- Generate decorated QR SVGs for each generated page and inject them between the QR markers
- Upload the generated `public/` folder to your Pages provider (Cloudflare Pages or GitHub Pages)

### Option 2: Local Development Setup

For contributors or advanced users who want to run scripts locally:

```bash
# Clone the repository
git clone https://github.com/YOUR-USERNAME/SimpleWish.git
cd SimpleWish

# Run the setup script (Linux/Mac)
./setup.sh

# Or manually set up (all platforms)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r scripts/requirements.txt
pip install -r scripts/requirements-dev.txt

# Run tests to verify
python3 -m pytest
```

## 📝 Customization

### Example Files

- `index.html` — Base template with classic green theme
- `elsa.html` — Example with blue theme and tech-focused gifts

### Personalizing Your Lists

When creating a list for someone (e.g., `elsa.html`):

1. **Update the title and header**:
   ```html
   <title>Elsa's Christmas List</title>
   <h1 id="recipient">Christmas List for Elsa</h1>
   ```

2. **Add gift ideas**:
   ```html
   <ul id="gift-list" class="gift-list">
     <li><a href="https://example.com/item" target="_blank" rel="noopener">Item description</a></li>
   </ul>
   ```

3. **Customize colors** (optional) - See "Customizing Colors" section below

### Customizing Colors

You can easily customize the page theme by editing the CSS variables at the top of the `<style>` section. Look for the clearly marked customization section:

**Page Theme Colors (edit in `<style>` section):**
```css
/* 🎨 CUSTOMIZE YOUR THEME HERE - Change these color values! */
:root{
  --bg:#f6f8fb;          /* Page background color */
  --card:#fff;           /* Card/paper background */
  --accent:#1565C0;      /* Accent color (headings, links) */
  --muted:#546E7A;       /* Muted text (subtitles, hints) */
  ...
}
```

**QR Code Customization (via meta tags in `<head>` section):**
```html
<!-- QR Code Colors -->
<meta name="qr-foreground-color" content="#1565C0">
<meta name="qr-background-color" content="#E3F2FD">

<!-- QR Decoration (true/false) -->
<meta name="qr-decorate" content="true">

<!-- Decoration Type (choose one) -->
<meta name="qr-decoration-type" content="tree">  
<!-- Options: tree, snowman, santa, gift, star, candy-cane, bell -->

<!-- Tree Style (only applies to tree decoration) -->
<meta name="qr-tree-style" content="fancy">
<!-- Options: fancy (with ornaments), plain (simple) -->
```

**Available Decoration Types:**
- 🎄 **tree** - Christmas tree (default) - supports `fancy` and `plain` styles
- ⛄ **snowman** - Classic snowman with hat and scarf
- 🎅 **santa** - Santa Claus face
- 🎁 **gift** - Wrapped present with bow
- ⭐ **star** - Decorative Christmas star
- 🍬 **candy-cane** - Striped candy cane
- 🔔 **bell** - Christmas bell with ribbon

**Example:** The `elsa.html` file uses a blue theme and a snowman:
- Page CSS: `--accent:#1565C0` (blue for headings/links)
- QR Code Color: `<meta name="qr-foreground-color" content="#1565C0">`
- Snowman Code: `<meta name="qr-decoration-type" content="snowman">`

**Color Palette Ideas:**
- 🔴 Classic Red: `#b71c1c` (default)
- 🔵 Tech Blue: `#1565C0` (alice.html example)
- 💚 Forest Green: `#2e7d32`
- 💜 Royal Purple: `#6a1b9a`
- 🧡 Warm Orange: `#e65100`

**Where to Edit:**
1. Open your HTML file in any text editor
2. Find the `<style>` section near the top (line ~16)
3. Look for the comment: `/* 🎨 CUSTOMIZE YOUR THEME HERE */`
4. Change the color hex codes to your preferred colors
5. Optionally update QR code colors in the `<meta>` tags

## 🖨️ Printing

1. Open the HTML file in your browser
2. Use Print (Ctrl+P / Cmd+P) or "Save as PDF"
3. The layout is optimized for printing with:
   - QR code pinned to top-right
   - Footer fixed at bottom
   - Clean, minimal design

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## 📄 License

This project is licensed under the **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License** (CC BY-NC-SA 4.0) - see the [LICENSE](LICENSE) file for details.

**Key Terms**:
- ✅ Free to use for personal, educational, and non-commercial purposes
- ✅ Can modify and adapt the code
- ✅ Must include attribution to this repository
- ✅ Share modifications under the same license
- ❌ **NO commercial use or profit-making without permission**

**Commercial Use**: If you want to sell this software, use it commercially, or make profit from it, you **must contact the author** (@zaxlofful) for permission.

**Free Use**: You're welcome to use, modify, and share this project freely for non-commercial purposes!

---

## Advanced Topics

### CI/CD with GitHub Actions

This repository includes automated workflows:
- **Lint** — Runs flake8 on Python code
- **pytest** — Runs pytest test suite
- **Generate QR** — Automatically generates and commits QR codes

**Copilot Trigger & Automation Label**

- **Trigger:** The repository's issue-based automation uses an issue body mention `@copilot` to trigger the Copilot workspace integration from workflows or scripts.
- **Local filtering:** The workflows apply a `todo-automation` label to automation issues so you can filter them locally (e.g., `is:issue label:todo-automation`). Workflows create this label idempotently if it is missing; to change this behavior, edit `.github/workflows/check-todo.yml`.


Copilot automation in CI (what the `check-todo` workflow does)

- The repository ships a scheduled workflow (`.github/workflows/check-todo.yml`) that automates TODO handling and can delegate work to GitHub Copilot.
- High-level behavior:
   - If `TODO.md` contains items, the workflow first checks for existing open issues labeled `todo-automation` to avoid duplicates.
   - It then checks for existing Pull Requests (open and recently closed) that look like Copilot work — it matches by PR author (`copilot-swe-agent`), `todo-automation` label, a title pattern like "Process TODO.md items", or by finding a short snippet of `TODO.md` in the PR body. Closed-but-merged PRs are ignored; closed-but-unmerged PRs are treated as existing to avoid reopening duplicate work.
   - The workflow logs the installed `gh` CLI version and whether `gh agent-task` is available in the runner (useful for debugging and diagnosing why the agent path was or wasn't used).
   - If no existing issue or PR is found and `gh agent-task` is available, the workflow prefers `gh agent-task create` to start a Copilot agent session directly from the TODO body (this avoids creating a separate issue in many cases).
   - If `gh agent-task` is not available or the agent task fails, the workflow falls back to creating a `todo-automation` issue, assigns it to the repository owner, and posts an `@copilot` comment so Copilot can be triggered when available.

- Secrets/permissions: the workflow uses the built-in `GITHUB_TOKEN` for repository operations (creating issues, comments, labels). No extra user token is required by default. To use the `gh agent-task` path in CI, ensure the runner has a reasonably recent `gh` (v2.80.0+ recommended) installed so the `agent-task` command exists and behaves as expected.

- Why this helps: the combination of detecting existing PRs (including recent closed-but-unmerged Copilot PRs), preferring the agent task when available, and having a simple fallback keeps automation idempotent and avoids duplicate issues/PRs while still making Copilot integration convenient.

### Deployment Options

This repository is designed to work with **Cloudflare Pages** and custom domains. The single-file HTML design makes deployment simple:

1. **Cloudflare Pages** (Recommended):
   - Connect your repository to Cloudflare Pages through their web GUI
   - **Important for security**: Configure to deploy only HTML files:
     - Build command: `mkdir public && find . -maxdepth 1 -type f -name '*.html' -print0 | xargs -0 -I {} cp -- '{}' public/`
     - Output directory: `public`
   - Why this matters: Cloudflare Pages will only deploy what's in the `public` folder, preventing accidental exposure of scripts, configuration files, or other repository contents
   - Note: This same command is used in the GitHub Pages workflow (`.github/workflows/deploy-pages.yml`)
   - Your lists will be available at your custom domain

2. **GitHub Pages** (Optional):
   - A manual workflow is available if you prefer GitHub Pages
   - Go to Actions → "Deploy to GitHub Pages (Optional)" → Run workflow
   - The workflow uses the same security approach: copying only HTML files to a `public` directory before deployment
   - Enable GitHub Pages in repository settings if needed

3. **Self-hosted**:
   - Simply copy the HTML files to any web server
   - No build process required
   - Recommended: Copy only `*.html` files for security

### Per-file Metadata

The QR generation script reads metadata from HTML files:

- `qr-foreground-color` — QR module color
- `qr-background-color` — QR background color
- `qr-decorate` — Enable/disable Christmas tree decoration
- `qr-tree-style` — `fancy` (with baubles) or `plain`

### Privacy

- No external tracking
- No CDN dependencies
- QR codes generated locally (no calls to remote services)
- All assets embedded in the HTML file

### Clean URLs

When adding gift links, remove tracking parameters:
- ❌ `https://example.com/product?utm_source=email&ref=tracker`
- ✅ `https://example.com/product`

Or...Add your own to track if they opened your links!

---

## CI Image and Secure Runners

This is a template (consider renaming the repo when you clone it)
- Intended workflow:
	1. Clone this repo as a template.
	2. Create one HTML file per person by copying `index.html` (e.g. `alice.html`, `bob.html`).
	3. Use a CI job to generate and embed a per-page QR SVG into each file based on the filename and your public root domain. This keeps each file single-file and offline-friendly.

Files
- `index.html` — the starter single-file template. Copy and edit per recipient.

QR code approach and single-file guarantee
- Keep QR artwork embedded in each HTML file. Preferred formats:
	- Inline SVG fragments, or
	- Data-URI images: `data:image/svg+xml;utf8,...`
- Embedding QR images in the page preserves the single-file guarantee (no runtime network calls or JS required).

Per-file metadata (`qr-foreground-color`, `qr-background-color`) are used by the generator when present and otherwise the CLI defaults are used.

Generating/updating SVGs via CI (recommended)
- Use CI (GitHub Actions or other) to generate per-page QR images and inject them into the corresponding HTML files before publishing.

Note on CLI defaults: The Python generator (`scripts/generate_qr_svg.py`) will read `ROOT_DOMAIN` from the environment if provided; otherwise it falls back to `https://example.com`. When building per-file public URLs the script appends the filename, so the effective fallback is `https://example.com/index.html` when run against `index.html` without configuration.

Local run examples
If you want to run the generator locally and ensure it uses your domain, set `ROOT_DOMAIN` in your shell and run the generator. Two examples below (POSIX shell and PowerShell):

POSIX / macOS / Linux (bash/zsh):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
export ROOT_DOMAIN="https://yourdomain.example"
python3 scripts/generate_qr_svg.py --pattern "*.html" --out-dir scripts/generated_qr
python3 scripts/inject_qr_svg.py --svg-dir scripts/generated_qr --pattern "*.html"
```

Windows PowerShell:
```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
pip install -r scripts/requirements.txt
$env:ROOT_DOMAIN = 'https://yourdomain.example'
python .\scripts\generate_qr_svg.py --pattern "*.html" --out-dir scripts/generated_qr
python .\scripts\inject_qr_svg.py --svg-dir scripts/generated_qr --pattern "*.html"
```

Notes:
- You can also pass `--root-domain` directly to `generate_qr_svg.py`; when `ROOT_DOMAIN` is set in the environment the CLI will use that by default so the explicit flag is optional.
- High-level CI flow:
	1. Discover per-recipient files (e.g. `alice.html`, `bob.html`) in the repo.
	2. Map each filename to its public URL: `https://<root-domain>/<filename>` (ensure filenames are URL-safe).
	3. Generate a QR SVG for that URL using a CLI or small script (`segno`, `qrcode`, `qrencode`, Node libs, etc.).
	4. Place the SVG (inline) or data-URI into the `.qrcode-box` region of that HTML file (use a clear marker comment so replacements are idempotent).
	5. Commit the modified files back to the repo from CI.

Notes on filenames and domain mapping
- Keep per-person filenames URL-safe (lowercase, hyphens; no spaces).
- CI scripts should be deterministic and idempotent so repeated runs don't create diffs.

Cleaning gift URLs
- If you include external product links in the list, remove tracking parameters (UTM, affiliate IDs) and other trackers before publishing. Prefer canonical clean links in the HTML.

How to preview / use locally
1. Open any per-person HTML file in a browser (double-click or run a tiny server).
2. Edit content directly in the file (or add `contenteditable="true"` if you want in-browser editing; update README when you do).
3. Print or save as PDF.

Privacy
- No external tracking is included by default. The CI-based QR injection pattern avoids runtime calls to remote QR generators. If you add remote scripts or CDNs, document the privacy tradeoffs in this README.


### Generating QR Codes

The repository includes Python scripts to generate and inject QR codes into your HTML files.

**Two-step process:**

```bash
# 1. Generate QR SVG files
python3 scripts/generate_qr_svg.py --root-domain "https://yourusername.github.io/SimpleWish" --pattern "*.html" --out-dir scripts/generated_qr

# 2. Inject QR codes into HTML files
python3 scripts/inject_qr_svg.py --svg-dir scripts/generated_qr --pattern "*.html"
```

**Customization options:**

```bash
# Use custom colors
python3 scripts/generate_qr_svg.py \
  --root-domain "https://example.com" \
  --pattern "*.html" \
  --out-dir scripts/generated_qr \
  --foreground-color "#1565C0" \
  --background-color "#E3F2FD"

# Disable decoration
python3 scripts/generate_qr_svg.py \
  --root-domain "https://example.com" \
  --pattern "*.html" \
  --out-dir scripts/generated_qr \
  --no-decorate

# Use plain tree style
python3 scripts/generate_qr_svg.py \
  --root-domain "https://example.com" \
  --pattern "*.html" \
  --out-dir scripts/generated_qr \
  --tree-style plain
```

See `python3 scripts/generate_qr_svg.py --help` for all options.

## CI image and secure runner notes

- This repository builds and publishes a minimal Debian-based CI image to GitHub Container Registry (GHCR) and uses that curated image for all CI runs on Linux runners. The image is built from `.github/ci/Dockerfile` (using `python:3.11-slim`) and pushed to `ghcr.io/<owner>/simplewish-ci:<sha>` and `:main` by the automated build workflow.
- Workflows pin to the `main` image tag and the SHA-tagged image for immutability. Cryptographic signing was previously used but has been removed from the automated build workflow and will be rethought.
  
TODO: Re-evaluate image signing and verification
- The repository previously used `cosign` (keyless) to sign published images. That signing step has been removed from the automated build workflow. Consider one of the following approaches in future iterations:
	- Reintroduce cosign with a vetted key-management approach (e.g., short-lived KMS-backed keys and GitHub OIDC), or
	- Use GitHub Container Registry immutability settings and repository variables to pin approved SHA tags, and document a manual verification procedure.
  
For now the CI image workflow publishes an image tagged with the commit SHA and, when on `main`, a `:main` tag; consuming workflows should pin to the SHA tag exposed via the `CI_IMAGE_TAG` repository variable.

Note about CI workflow linter warnings
- You may see linter/editor warnings about `vars.CI_IMAGE_TAG` being unavailable for `container.image` at workflow-compile time. These are expected because the variable is created by the build workflow and may not exist at compile-time for consumer workflows. The repository intentionally uses `workflow_run` and fallbacks to ensure jobs run even when the variable is not set.

Build and publish the CI image (done automatically on push to `main`):

```bash
# Build locally (optional)
docker build -f .github/ci/Dockerfile -t ghcr.io/$GITHUB_ACTOR/simplewish-ci:local .

# Push (requires GHCR login)
docker tag ghcr.io/$GITHUB_ACTOR/simplewish-ci:local ghcr.io/<owner>/simplewish-ci:main
docker push ghcr.io/<owner>/simplewish-ci:main
```

Security notes:
- The CI image is pinned by tag in workflows; for fully immutable runs the image is also published with the commit SHA as a tag (the build workflow does this).
- The build workflow also runs a vulnerability scan (Trivy). Image signing via `cosign` was previously used but is not performed by the automated build workflow anymore.
- CI currently runs on Linux runners only and uses the curated GHCR image to minimize runtime attack surface. If you need stricter isolation, consider ephemeral self-hosted runners in a locked-down VPC.


Enjoy! Happy holidays.