## Purpose
This repository is a tiny, single-file static HTML template for printable Christmas gift lists. These instructions help an AI coding agent be productive quickly: understand the minimal architecture, the QR injection workflow, and safe edits that preserve the single-file, GitHub-Pages-friendly output.

## Quick high-level summary
- Single artifact per recipient: <filename>.html (starter: `index.html`).
- No build system. Styling & layout are inlined in `index.html` for portability and print fidelity.
- QR artwork is embedded inline between explicit markers; CI scripts in `scripts/` generate and inject QR SVGs.
 - Requirements: scripts are Python-based. Use a virtualenv and install dependencies from `scripts/requirements.txt`. The project was developed with CPython 3.13 artifacts present; Python 3.10+ is recommended.

## Key files and markers (read these before editing)
- `index.html` — single-file template. Look for the QR marker comments exactly as below:
  - `<!-- QR-PLACEHOLDER-START -->` and `<!-- QR-PLACEHOLDER-END -->`
  - The QR element lives inside `.qrcode-box`. The CSS expects a 250×250 element (`.qrcode-box svg, .qrcode-box img, #qrcode`).
`README.md`  usage, privacy notes, and high-level CI guidance.
- `scripts/generate_qr_svg.py`  generates per-file SVG files to an output directory (`scripts/generated_qr`).
- `scripts/inject_qr_svg.py`  takes SVGs from `scripts/generated_qr` and injects them into HTML files between the QR markers.

## Project-specific workflows (concrete, copy-paste examples)
Two-step: produce SVGs then inject (useful for review or separate CI jobs):
  1. python scripts/generate_qr_svg.py --root-domain "https://example.com" --pattern "*.html" --out-dir scripts/generated_qr
  2. python scripts/inject_qr_svg.py --svg-dir scripts/generated_qr --pattern "*.html"

Notes on flags you'll likely need:
`generate_qr_svg.py` supports `--no-decorate` (decoration is enabled by default), `--foreground-color` (alias `--foreground`), `--background-color` (alias `--background`), `--logo-size`, `--overlay-mult`, `--overlay-shift-x`, `--overlay-shift-y`, and `--ecc` for QR generation tuning. When decorating, the decorative tree/logo is placed in the bottom-right overlay by design; its exact placement can be nudged with the overlay shift flags.
`inject_qr_svg.py` has `--preserve-manual` to skip replacing manually edited placeholders.

Also note: `generate_qr_svg.py` recognizes an additional per-file meta key `qr-decoration-type` (and the existing `qr-tree-style`) to choose the decoration variant. The generator will emit SVGs with class `qr-svg` and a `data-qr-default-foreground-color` attribute. The SVG modules use currentColor, so page CSS can recolor the QR by setting `.qr-svg { color: #... }` — the data attribute contains the original/default color.

## Per-file meta tags and how the generator uses them
-- The HTML may include meta tags the generators read to adjust color/decoration. Look for examples in `index.html` header comments. Supported keys (checked by scripts): `qr-foreground-color`, `qr-background-color`, `qr-decorate`, `qr-tree-style`, `qr-decoration-type`.
  - Example:
    <meta name="qr-foreground-color" content="#0b6623">
    <meta name="qr-background-color" content="#ffffff">
    <meta name="qr-decorate" content="true">
    <meta name="qr-tree-style" content="fancy">

Note: legacy meta names such as `qr-foreground` and `qr-background` have been removed from the generator; use the canonical `-color` names above.

Generator output note: when `generate_qr_svg.py` writes SVGs it:
- adds class `qr-svg` to the root `<svg>`
- includes `data-qr-default-foreground-color="#xxxxxx"` with the color used when generating
- uses CSS `currentColor` in modules where practical so authors can override the QR color with CSS like `.qr-svg { color: #b71c1c; }`.

Available decoration types:
- `tree` (default) — supports `fancy` and `plain` styles via `qr-tree-style` or `--tree-style`.
- `snowman` — classic snowman with hat and scarf.
- `santa` — Santa Claus face.
- `gift` — wrapped present with bow.
- `star` — decorative star.
- `candy-cane` — striped candy cane.
- `bell` — bell with ribbon.

Programmatic API & helper functions (useful for maintainers or custom tooling):
- `read_meta_tags_from_html(path)` — returns a dict of per-file QR meta keys found in an HTML file (used by the CLI to honor `qr-...` meta tags).
- `generate_svg(url, ..., decoration_type='tree', tree_style='fancy', ...)` — main helper that produces an embeddable SVG string for a given URL. It accepts the same high-level options as the CLI (foreground/background, decorate, ecc, logo sizing/placement, decoration type/style) and returns an inline SVG already prepared for injection (it also adds `class="qr-svg"` and the `data-qr-default-foreground-color` attribute).
- `sanitize_svg_for_html(svg)` — strips XML prolog/doctype so the SVG is safe to embed in HTML documents.
- `clean_filename_to_path(filename)` — URL-encodes filenames when building public URLs.
- Decoration getters: `get_tree_decoration(style)`, `get_snowman_decoration()`, `get_santa_decoration()`, `get_gift_decoration()`, `get_star_decoration()`, `get_candy_cane_decoration()`, `get_bell_decoration()` — return SVG fragment strings used by `generate_svg`.

CLI flags map to these programmatic options (examples): `--decoration-type` maps to `decoration_type`, `--tree-style` maps to `tree_style`, `--overlay-mult`/`--overlay-shift-x`/`--overlay-shift-y` control overlay placement, `--logo-size` controls reserved area size, and `--ecc` sets the QR error-correction level.

## Patterns and conventions to preserve
- Single-file guarantee: prefer inline SVG or data-URI images for QR artwork so each generated HTML file can be opened standalone.
- Filenames map directly to public URLs: CI must use URL-safe filenames (lowercase, hyphens). The scripts use urllib.quote on the filename when building the public URL.
- Marker-based idempotence: the scripts look for the exact marker comments shown above; keep them unchanged if you intend to use the automation.
  - Markers are matched exactly and literally: `<!-- QR-PLACEHOLDER-START -->` and `<!-- QR-PLACEHOLDER-END -->`. Do not add extra text on the same line or change case/spacing; the injector is sensitive to the exact marker string.
- CSS expectations: the layout reserves a 250×250 right-side QR in print. If you change the QR element id/class, update CSS selectors (`.qrcode-box svg, .qrcode-box img, #qrcode`) and the scripts' expectations.

## Safe edit examples (concrete)
- Make recipient editable in-place (small, well-scoped change):
  - Edit `index.html` and change `<h1 id="recipient">` to `<h1 id="recipient" contenteditable="true">` and update `README.md` to document in-browser editing.
- Replace placeholder with a data-URI image (keeps single-file):
  - Remove the inline placeholder SVG between the markers and insert `<img src="data:image/svg+xml;utf8,..." class="qr-svg" data-qr-default-foreground="#0b6623">`. Ensure size and id/class follow CSS selectors.

## What to avoid / gotchas (concrete)
 - Don't rename or remove the QR markers unless you also update the scripts. The generator relies on those exact strings.
 - The repo's `index.html` currently contains an embedded demo SVG that includes the string "ChristmasList"; some automation scripts will skip replacing such protected SVGs unless explicitly overridden — remove the marker content manually or use the generator's override flag when available.
- If you introduce external assets (CDNs, remote JS), update the README and call out privacy tradeoffs — the project intentionally ships fully static pages.

## Minimal review checklist for PRs created by agents
- Confirm altered HTML files still open standalone in a browser (no network assets required).
- If you changed QR behavior, run the exact script(s) you mention in the PR description and include sample output or a small screenshot of the printed layout.
- Ensure any per-file meta-tag changes are documented in `README.md`.

Quick test run for maintainers: from the repo root (activate your venv) run:

```powershell
python -m pytest tests/test_generate_svg.py
```

This validates that meta parsing and data-attribute emission are working as expected.

## Quick troubleshooting notes for maintainers
- "Markers not found" when running scripts: ensure the file contains the exact marker comments and they are not commented out or modified.
 - "Protected embedded SVG detected": some scripts may skip files that contain 'ChristmasList' in the placeholder; remove the marker content manually or use the appropriate override flag in the generating script.
- If injected SVG doesn't indent correctly, `inject_qr_svg.py` detects indentation and matches the marker line; it uses a tab if the marker line contains tabs, otherwise 4 spaces.

If you need to change the default QR color in-browser without regenerating the SVG, add a small rule to the page CSS such as:

```css
.qr-svg { color: #b71c1c; } /* recolors QR modules where the SVG uses currentColor */
```

## Where to look next (useful files)
## GitHub Actions workflows
This repository includes several GitHub Actions workflows that power CI, testing, image builds, QR generation, and optional deployments. Read the workflow YAML files in `.github/workflows/` before editing CI logic.

- `build-ci-image.yml` — Build and publish CI images to GHCR (produces `simplewish-qr` and `simplewish-infra`). Trigger: `push` to `main` and manual (`workflow_dispatch`). Other workflows use these images as containers.
-- `lint.yml` — Run flake8 inside the infra container. Trigger: manual or after the Build workflow completes successfully (uses `workflow_run`).
-- `pytest.yml` — Run pytest inside the infra container. Trigger: manual or after the Build workflow completes successfully.
-- `pr-ci.yml` — (removed) Previously provided a combined PR check; lint and test workflows now run individually on PRs.
- `generate-qrs.yml` — Generate QR SVGs and inject them into HTML files, then commit changes. Trigger: manual or after the CI image build completes successfully. Important: this workflow reads the `ROOT_DOMAIN` repo variable/secret to build public URLs and runs inside the `simplewish-qr` container.
- `deploy-pages.yml` — Optional, manual deployment to GitHub Pages. It intentionally copies only `*.html` to a `public/` folder before uploading to Pages. Trigger: manual (`workflow_dispatch`).

Notes:
- Many workflows are written to be safe (they use container images from GHCR and `workflow_run` sequencing). If you change the image names or tags, update dependent workflows accordingly.
- `generate-qrs.yml` expects a repository-level `ROOT_DOMAIN` secret or variable (recommended). If not present it falls back to `https://example.com` in the workflow.
 - `generate-qrs.yml` expects a repository-level `ROOT_DOMAIN` secret or variable (recommended). If not present it falls back to `https://example.com` in the workflow. The workflow sets `ROOT_DOMAIN` with precedence: default (`https://example.com`) -> repo variable `ROOT_DOMAIN` -> secret `ROOT_DOMAIN` (secret overwrites variable).

Note: the Python CLI `scripts/generate_qr_svg.py` also checks the `ROOT_DOMAIN` environment variable and will default to `https://example.com` if nothing is provided; when used against `index.html` the effective fallback URL is `https://example.com/index.html`.

Quick local run (set ROOT_DOMAIN and run generator):

POSIX:
```bash
export ROOT_DOMAIN="https://yourdomain.example"
python3 scripts/generate_qr_svg.py --pattern "*.html" --out-dir scripts/generated_qr
python3 scripts/inject_qr_svg.py --svg-dir scripts/generated_qr --pattern "*.html"
```

PowerShell:
```powershell
$env:ROOT_DOMAIN = 'https://yourdomain.example'
python .\scripts\generate_qr_svg.py --pattern "*.html" --out-dir scripts/generated_qr
python .\scripts\inject_qr_svg.py --svg-dir scripts/generated_qr --pattern "*.html"
```
- The `deploy-pages.yml` workflow uses `concurrency` and special Pages permissions — review it before enabling automatic runs.
- `index.html` — layout, markers, and example QR placeholder
- `README.md` — user-facing instructions and privacy notes
 - `scripts/generate_qr_svg.py`, `scripts/inject_qr_svg.py` — canonical automation scripts (read before modifying CI)