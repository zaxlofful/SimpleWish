# Repository guide

SimpleWish is a static HTML template for printable Christmas gift lists. The HTML pages remain standalone; Rust is used for generation and repository automation.

## Structure

- `index.html` is the starter page; per-recipient data lives in `recipients/*.json`.
- `src/` contains the `simplewish` Rust CLI and its unit tests.
- `tests/reference_*.svg` are deterministic output fixtures.
- `scripts/generated_qr/` is the default output directory for QR SVG generation.

## Rust CLI

Use `cargo run --release -- <command> --help` for command usage. Main commands:

- `generate-recipient --bulk --recipients-dir recipients`
- `generate-qr --root-domain "https://example.com" --pattern "*.html" --out-dir scripts/generated_qr`
- `inject-qr --svg-dir scripts/generated_qr --pattern "*.html"`
- `check-todo`, `update-todo-from-prs`, `render-readme`, `check-svg`
- `regenerate-reference`

The QR generator recognizes `qr-foreground-color`, `qr-background-color`, `qr-decorate`, `qr-tree-style`, and `qr-decoration-type` meta tags. Decoration types are tree, snowman, santa, gift, star, candy-cane, and bell; tree styles are fancy and plain.

The SVG injector requires the literal markers `<!-- QR-PLACEHOLDER-START -->` and `<!-- QR-PLACEHOLDER-END -->`. Preserve these strings and the `.qrcode-box` sizing rules in `index.html`.

## Development

Install stable Rust with the `rustfmt` and `clippy` components. Validate changes with:

```sh
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all
```

`./setup.sh --build` renders recipient pages, creates and injects QR SVGs, and places HTML files in `public/`. Keep external assets out of the pages so the standalone-file and privacy guarantees remain intact.
