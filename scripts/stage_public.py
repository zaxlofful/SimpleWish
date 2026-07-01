#!/usr/bin/env python3
"""Stage only index.html and recipient-derived HTML for deployment."""

import argparse
import shutil
from pathlib import Path


def confined_path(root: Path, value: str, label: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f'{label} must stay within repository root') from exc
    if candidate == root:
        raise ValueError(f'{label} must not be repository root')
    return candidate


def stage_public(
    root: Path,
    recipients_dir: str,
    public_dir: str,
) -> list[Path]:
    root = root.resolve()
    recipients = confined_path(root, recipients_dir, 'recipients directory')
    public = confined_path(root, public_dir, 'public directory')

    names = {'index.html'}
    if recipients.is_dir():
        names.update(
            path.with_suffix('.html').name
            for path in recipients.glob('*.json')
        )

    public.mkdir(parents=True, exist_ok=True)
    for stale_html in public.glob('*.html'):
        if stale_html.is_file() or stale_html.is_symlink():
            stale_html.unlink()
        else:
            raise ValueError(
                f'cannot replace non-file output {stale_html}'
            )

    staged = []
    for name in sorted(names):
        source = root / name
        if not source.exists():
            continue
        try:
            source.resolve().relative_to(root)
        except ValueError as exc:
            raise ValueError(f'HTML source escapes repository: {name}') from exc
        destination = public / name
        shutil.copy2(source, destination)
        staged.append(destination)
    return staged


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default='.')
    parser.add_argument('--recipients-dir', default='recipients')
    parser.add_argument('--public-dir', default='public')
    args = parser.parse_args()

    try:
        staged = stage_public(
            Path(args.root),
            args.recipients_dir,
            args.public_dir,
        )
    except ValueError as exc:
        parser.error(str(exc))

    for path in staged:
        print(f'Staged {path}')
    print(f'Staged {len(staged)} HTML file(s)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
