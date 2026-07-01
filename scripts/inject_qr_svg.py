#!/usr/bin/env python3
"""
Inject SVG QR files produced by generate_qr_svg.py into HTML files between
QR markers.

Usage:
    python scripts/inject_qr_svg.py --svg-dir scripts/generated_qr \
            --pattern "*.html"

Matches each <basename>.svg to <basename>.html and injects the SVG between
the markers.
"""
import argparse
import glob
import os
import re
from xml.etree import ElementTree

MARKER_START = '<!-- QR-PLACEHOLDER-START -->'
MARKER_END = '<!-- QR-PLACEHOLDER-END -->'
SVG_NAMESPACE = 'http://www.w3.org/2000/svg'
ALLOWED_SVG_TAGS = {
    'circle',
    'ellipse',
    'g',
    'path',
    'polygon',
    'rect',
    'svg',
}
ALLOWED_SVG_ATTRIBUTES = {
    'aria-hidden',
    'class',
    'cx',
    'cy',
    'd',
    'data-qr-default-foreground-color',
    'fill',
    'height',
    'id',
    'opacity',
    'points',
    'r',
    'rx',
    'ry',
    'stroke',
    'stroke-linecap',
    'stroke-linejoin',
    'stroke-width',
    'transform',
    'viewBox',
    'width',
    'x',
    'y',
}
DANGEROUS_SVG_VALUE_RE = re.compile(
    r'(?:url\s*\(|javascript\s*:|data\s*:)',
    re.IGNORECASE,
)


def _qualified_name(name: str) -> tuple[str, str]:
    if name.startswith('{'):
        namespace, local_name = name[1:].split('}', 1)
        return namespace, local_name
    return '', name


def validate_svg(svg_content: str) -> None:
    """Reject markup outside the generator's static SVG subset."""
    if re.search(r'<!DOCTYPE|<!ENTITY|<\?', svg_content, re.IGNORECASE):
        raise ValueError('unsafe SVG declaration')
    try:
        root = ElementTree.fromstring(svg_content)
    except ElementTree.ParseError as exc:
        raise ValueError('unsafe SVG: invalid XML') from exc

    root_namespace, root_name = _qualified_name(root.tag)
    if root_name != 'svg' or root_namespace not in {'', SVG_NAMESPACE}:
        raise ValueError('unsafe SVG root element')

    for element in root.iter():
        namespace, tag = _qualified_name(element.tag)
        if namespace != root_namespace or tag not in ALLOWED_SVG_TAGS:
            raise ValueError(f'unsafe SVG element: {tag}')
        for raw_attribute, value in element.attrib.items():
            attribute_namespace, attribute = _qualified_name(raw_attribute)
            if (
                attribute_namespace
                or attribute not in ALLOWED_SVG_ATTRIBUTES
            ):
                raise ValueError(f'unsafe SVG attribute: {attribute}')
            if DANGEROUS_SVG_VALUE_RE.search(value):
                raise ValueError(f'unsafe SVG value in {attribute}')


def inject(svg_content: str, html_path: str, preserve_manual: bool = False) -> bool:
    validate_svg(svg_content)

    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    start_idx = content.find(MARKER_START)
    end_idx = content.find(MARKER_END)
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        print(f'Markers not found in {html_path}; skipping')
        return False

    existing_block = content[start_idx + len(MARKER_START):end_idx]
    # If requested, preserve manual edits: skip replacement when the placeholder
    # already contains any non-whitespace (i.e. someone manually edited it).
    # --force overrides.
    if preserve_manual and existing_block.strip():
        print(f'Manual content detected in {html_path}; skipping.')
        return False

    # Detect indentation of the marker's line and match it.
    # If the file uses tabs at the marker line, add one tab; otherwise add
    # four spaces.
    start_line_start = content.rfind('\n', 0, start_idx) + 1
    marker_line = content[start_line_start:start_idx]
    m_ws = re.match(r'^([ \t]*)', marker_line)
    leading_ws = m_ws.group(1) if m_ws else ''
    # Use the same leading whitespace as the marker line so the injected
    # SVG aligns with the marker. Do not add an extra level of indentation
    # — keep the injected lines starting at the same column as the marker.
    indent = leading_ws
    # Prefix each line of the SVG with the chosen indent. Preserve blank
    # lines as empty lines.
    # Prefix each non-empty line of the SVG with the chosen indent and
    # skip blank lines entirely to avoid excessive vertical whitespace
    # introduced by XML pretty-printers.
    indented_svg = '\n'.join(
        (indent + line)
        for line in svg_content.splitlines()
        if line.strip() != ''
    )
    # Use the same leading whitespace as the start marker so the start/end markers align.
    end_line_leading = leading_ws

    # Insert the indented SVG and then re-insert the start-marker leading
    # whitespace before the end marker
    parts = [
        content[: start_idx + len(MARKER_START)],
        '\n',
        indented_svg,
        '\n',
        end_line_leading,
        content[end_idx:],
    ]
    new_content = ''.join(parts)

    if new_content == content:
        print(f'No changes for {html_path}')
        return False

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f'Injected SVG into {html_path}')
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--svg-dir', required=True)
    parser.add_argument('--pattern', default='*.html')
    parser.add_argument(
        '--preserve-manual',
        action='store_true',
        help=(
            'Skip replacing placeholder if it already contains '
            'non-whitespace (manual edits)'
        ),
    )
    args = parser.parse_args()

    svgs = glob.glob(os.path.join(args.svg_dir, '*.svg'))
    if not svgs:
        print('No SVG files found to inject')
        return 0

    updated = 0
    for svg_path in svgs:
        basename = os.path.splitext(os.path.basename(svg_path))[0]
        html_path = f'{basename}.html'
        if not os.path.exists(html_path):
            print(f'No matching HTML file for {svg_path}; expected {html_path}; skipping')
            continue
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        if inject(svg_content, html_path, preserve_manual=args.preserve_manual):
            updated += 1

    print(f'Done — injected into {updated} files')


if __name__ == '__main__':
    raise SystemExit(main())
