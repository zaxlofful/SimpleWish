````instructions
## Purpose
This repository is a tiny, single-file static HTML template for printable Christmas gift lists. These instructions help an AI coding agent be productive quickly: understand the minimal architecture, the QR injection workflow, and safe edits that preserve the single-file, GitHub-Pages-friendly output.

## Quick high-level summary
- Single artifact per recipient: <filename>.html (starter: `index.html`).
- No build system. Styling & layout are inlined in `index.html` for portability and print fidelity.
- QR artwork is embedded inline between explicit markers; CI scripts in `scripts/` generate and inject QR SVGs.

## Key files and markers (read these before editing)
- `index.html` — single-file template. Look for the QR marker comments exactly as below:
  - `<!-- QR-PLACEHOLDER-START -->` and `<!-- QR-PLACEHOLDER-END -->`
  - The QR element lives inside `.qrcode-box`. The CSS expects a 250×250 element (`.qrcode-box svg, .qrcode-box img, #qrcode`).
- `README.md` — usage, privacy notes, and high-level CI guidance.
 - `README.md` — usage, privacy notes, and high-level CI guidance.
 - `scripts/generate_qr_svg.py` — generates per-file SVG files to an output directory (`scripts/generated_qr`).
 - `scripts/inject_qr_svg.py` — takes SVGs from `scripts/generated_qr` and injects them into HTML files between the QR markers.

## Project-specific workflows (concrete, copy-paste examples)
Two-step: produce SVGs then inject (useful for review or separate CI jobs):
  1. python scripts/generate_qr_svg.py --root-domain "https://example.com" --pattern "*.html" --out-dir scripts/generated_qr
  2. python scripts/inject_qr_svg.py --svg-dir scripts/generated_qr --pattern "*.html"

Notes on flags you'll likely need:
`generate_qr_svg.py` supports `--no-decorate`, `--dark`, `--light`, `--transparent`, `--reserve-mode`, `--logo-position`, `--logo-size`, `--overlay-mult`, `--overlay-shift-x`, `--overlay-shift-y`, and `--ecc` for QR generation tuning.
`inject_qr_svg.py` has `--preserve-manual` to skip replacing manually edited placeholders.

## Per-file meta tags and how the generator uses them
- The HTML may include meta tags the generators read to adjust color/decoration. Look for examples in `index.html` header comments. Supported keys (checked by scripts): `qr-dark`, `qr-light`, `qr-decorate`, `qr-tree-style`.
  - Example:
    <meta name="qr-dark" content="#0b6623">
    <meta name="qr-decorate" content="true">
    <meta name="qr-tree-style" content="fancy">

## Patterns and conventions to preserve
- Single-file guarantee: prefer inline SVG or data-URI images for QR artwork so each generated HTML file can be opened standalone.
- Filenames map directly to public URLs: CI must use URL-safe filenames (lowercase, hyphens). The scripts use urllib.quote on the filename when building the public URL.
- Marker-based idempotence: the scripts look for the exact marker comments shown above; keep them unchanged if you intend to use the automation.
- CSS expectations: the layout reserves a 250×250 right-side QR in print. If you change the QR element id/class, update CSS selectors (`.qrcode-box svg, .qrcode-box img, #qrcode`) and the scripts' expectations.

## Safe edit examples (concrete)
- Make recipient editable in-place (small, well-scoped change):
  - Edit `index.html` and change `<h1 id="recipient">` to `<h1 id="recipient" contenteditable="true">` and update `README.md` to document in-browser editing.
- Replace placeholder with a data-URI image (keeps single-file):
  - Remove the inline placeholder SVG between the markers and insert `<img src="data:image/svg+xml;utf8,..." class="qr-svg" data-qr-default-color="#0b6623">`. Ensure size and id/class follow CSS selectors.

## What to avoid / gotchas (concrete)
 - Don't rename or remove the QR markers unless you also update the scripts. The generator relies on those exact strings.
 - The repo's `index.html` currently contains an embedded demo SVG that includes the string "ChristmasList"; some automation scripts will skip replacing such protected SVGs unless explicitly overridden — remove the marker content manually or use the generator's override flag when available.
- If you introduce external assets (CDNs, remote JS), update the README and call out privacy tradeoffs — the project intentionally ships fully static pages.

## Minimal review checklist for PRs created by agents
- Confirm altered HTML files still open standalone in a browser (no network assets required).
- If you changed QR behavior, run the exact script(s) you mention in the PR description and include sample output or a small screenshot of the printed layout.
- Ensure any per-file meta-tag changes are documented in `README.md`.

## Quick troubleshooting notes for maintainers
- "Markers not found" when running scripts: ensure the file contains the exact marker comments and they are not commented out or modified.
 - "Protected embedded SVG detected": some scripts may skip files that contain 'ChristmasList' in the placeholder; remove the marker content manually or use the appropriate override flag in the generating script.
- If injected SVG doesn't indent correctly, `inject_qr_svg.py` detects indentation and matches the marker line; it uses a tab if the marker line contains tabs, otherwise 4 spaces.

## Where to look next (useful files)
- `index.html` — layout, markers, and example QR placeholder
- `README.md` — user-facing instructions and privacy notes
 - `scripts/generate_qr_svg.py`, `scripts/inject_qr_svg.py` — canonical automation scripts (read before modifying CI)

## If anything is unclear
Tell me which section you want stricter rules for (for example: "always require `--force` on generate to prevent accidental overwrite") and I'll update this guidance.
````
