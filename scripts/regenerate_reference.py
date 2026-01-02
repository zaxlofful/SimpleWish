#!/usr/bin/env python3
"""Regenerate tests/reference_qr.svg using the current generator.

Run this with the project's venv Python so the output matches test expectations.
"""
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.generate_qr_svg import generate_svg, sanitize_svg_for_html
import scripts.generate_qr_svg as gen_module


def main():
    # Match CLI/test defaults used in tests
    gen_module.__overlay_multiplier__ = 3.0
    gen_module.__overlay_shift_x__ = 0.90
    gen_module.__overlay_shift_y__ = 0.50

    # Canonical index.html reference
    svg = generate_svg(
        url='https://example.com/index.html',
        foreground_color='#0b6623',
        background_color='#ffffff',
        decorate=True,
        border=0,
        logo_size_pct=20.0,
        logo_pos='bottom-right',
        reserve_mode='overlay',
        ecc='H',
        tree_style='fancy',
        decoration_type='tree',
    )

    embedded = sanitize_svg_for_html(svg, pretty=True, indent_spaces=2)

    ref_path = os.path.join(REPO_ROOT, 'tests', 'reference_qr.svg')
    with open(ref_path, 'w', encoding='utf-8') as f:
        f.write(embedded)

    print('Wrote updated reference to', ref_path)

    # Elsa-specific reference (snowman decoration and different colors)
    svg2 = generate_svg(
        url='https://example.com/elsa.html',
        foreground_color='#1565C0',
        background_color='#e3f2fd',
        decorate=True,
        border=0,
        logo_size_pct=20.0,
        logo_pos='bottom-right',
        reserve_mode='overlay',
        ecc='H',
        tree_style='fancy',
        decoration_type='snowman',
    )

    embedded2 = sanitize_svg_for_html(svg2, pretty=True, indent_spaces=2)
    ref_path2 = os.path.join(REPO_ROOT, 'tests', 'reference_elsa_qr.svg')
    with open(ref_path2, 'w', encoding='utf-8') as f:
        f.write(embedded2)

    print('Wrote updated elsa reference to', ref_path2)


if __name__ == '__main__':
    main()
