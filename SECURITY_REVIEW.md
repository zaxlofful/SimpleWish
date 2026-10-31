# SimpleWish security notes

The previous review covered Python scripts and Python-based CI images, all of which have been removed. This note describes the Rust implementation and is not a substitute for a dedicated security audit.

## Current input boundaries

- Recipient JSON is escaped before insertion into HTML. CSS accent and muted values are restricted to hexadecimal colors, and gift links are rendered only for `http`, `https`, and `mailto` URLs.
- QR metadata is read from local HTML. The QR encoder runs locally; generated SVGs are embedded without runtime network calls. The foreground value is escaped before it is written as an SVG attribute.
- The CLI accepts file paths for templates, inputs, outputs, and QR directories. Run it only with paths trusted by the invoking user.
- The QR injector inserts SVG content from its configured directory verbatim. Treat that directory as trusted input.
- `update-todo-from-prs` invokes the GitHub CLI and removes TODO lines when their words match completed-item text in merged PR bodies.
- CI runs Cargo checks and tests on hosted runners. Workflows that write issues or commit generated pages require the corresponding GitHub token permissions.

## Maintenance

Keep `Cargo.lock` checked in and review dependency advisories when dependencies change. Revisit these notes when new input sources, file writes, or workflow permissions are added.
