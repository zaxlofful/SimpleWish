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
- The generator now emits SVGs whose modules use currentColor; each injected SVG receives class `qr-svg` and a `data-qr-default-color` attribute containing the default color. To change QR color via CSS, add a rule such as:

```css
.qr-svg { color: #b71c1c; } /* makes the QR modules red */
```

Per-file metadata (`qr-dark`, `qr-light`) still work and are used as defaults by the generator when generating the SVG.

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

Enjoy! Happy holidays.