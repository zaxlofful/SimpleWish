# Contributing to SimpleWish

Thank you for contributing to this small, focused project for printable Christmas gift lists.

## Development setup

Install the stable Rust toolchain with the `rustfmt` and `clippy` components. Cargo downloads and builds the locked dependencies.

```sh
cargo test --all
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- -D warnings
```

## QR generation

```sh
cargo run --release -- generate-qr --root-domain "https://example.com" --pattern "*.html" --out-dir scripts/generated_qr
cargo run --release -- inject-qr --svg-dir scripts/generated_qr --pattern "*.html"
```

Use small, focused changes. Preserve the standalone HTML and print layout, the exact QR placeholder markers, and accessibility. Add or update Rust tests for behavioral changes.

## Pull requests

- Describe what changed and why.
- Include screenshots for visual changes.
- Ensure formatting, Clippy, and tests pass.
- Reference related issues when applicable.

By contributing, you agree that your contributions will be licensed under the same license as the project.
