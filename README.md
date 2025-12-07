![Lint](https://github.com/ZaxLofful/SimpleWish/actions/workflows/lint.yml/badge.svg)
![Test](https://github.com/ZaxLofful/SimpleWish/actions/workflows/test.yml/badge.svg)
![Generate QR](https://github.com/ZaxLofful/SimpleWish/actions/workflows/generate-qrs.yml/badge.svg)

Christmas list template (HTML + CSS)

What this is
- A printable, single-file HTML template intended to be used as a template for one-page gift lists per recipient.
- All styles are inlined in `index.html` so each generated page is fully self-contained and can be opened locally or hosted on GitHub Pages without build steps.

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


Coloring by CSS
- The generator now emits SVGs whose modules use currentColor; each injected SVG receives class `qr-svg` and a `data-qr-default-foreground-color` attribute containing the default color. To change QR color via CSS, add a rule such as:

```css
.qr-svg { color: #b71c1c; } /* makes the QR modules red */
```

Per-file metadata (`qr-foreground-color`, `qr-background-color`) are used by the generator when present and otherwise the CLI defaults are used.

Generating/updating SVGs via CI (recommended)
- Use CI (GitHub Actions or other) to generate per-page QR images and inject them into the corresponding HTML files before publishing.
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

Want a runnable example?
- The repo includes two small scripts to generate SVGs and then inject them: `scripts/generate_qr_svg.py` and `scripts/inject_qr_svg.py`.

Two-step quick example:
1. python scripts/generate_qr_svg.py --root-domain "https://example.com" --pattern "*.html" --out-dir scripts/generated_qr
2. python scripts/inject_qr_svg.py --svg-dir scripts/generated_qr --pattern "*.html"

- CLI highlights
- `--foreground-color` (default: #0b6623)
- `--background-color` (default: #ffffff)
- `--no-decorate` to disable the bottom-right decoration
- `--logo-size`, `--overlay-mult`, `--overlay-shift-x`, `--overlay-shift-y` to nudge placement

Enjoy! Happy holidays.

## Contributing

Small, focused changes are welcome. Typical workflow:

1. Fork and branch from `main`.
2. Run lint/tests locally (see `scripts/requirements-dev.txt`).
3. Open a PR describing the change and linking CI checks.

Keep changes small and preserve the single-file guarantee for per-recipient HTML files.

## Changelog (brief)

- 2025-12-07: First list made and workflows created

## CI image and secure runner notes

- This repository builds and publishes a minimal Alpine-based CI image to GitHub Container Registry (GHCR) and uses that curated image for all CI runs on Linux runners. The image is built from `.github/ci/Dockerfile` and pushed to `ghcr.io/<owner>/simplewish-ci:<sha>` and `:main` by the automated build workflow.
- Workflows pin to the `main` image tag and the SHA-tagged image for immutability. Cryptographic signing was previously used but has been removed from the automated build workflow and will be rethought.
  
TODO: Re-evaluate image signing and verification
- The repository previously used `cosign` (keyless) to sign published images. That signing step has been removed from the automated build workflow. Consider one of the following approaches in future iterations:
	- Reintroduce cosign with a vetted key-management approach (e.g., short-lived KMS-backed keys and GitHub OIDC), or
	- Use GitHub Container Registry immutability settings and repository variables to pin approved SHA tags, and document a manual verification procedure.
  
For now the CI image workflow publishes an image tagged with the commit SHA and, when on `main`, a `:main` tag; consuming workflows should pin to the SHA tag exposed via the `CI_IMAGE_TAG` repository variable.

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