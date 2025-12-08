import hashlib
import os

from scripts.generate_qr_svg import generate_svg, sanitize_svg_for_html
import scripts.generate_qr_svg as gen_module


def test_alice_qr_matches_reference():
    # Ensure overlay globals match CLI defaults
    gen_module.__overlay_multiplier__ = 3.0
    gen_module.__overlay_shift_x__ = 0.90
    gen_module.__overlay_shift_y__ = 0.50

    svg = generate_svg(
        url='https://example.com/alice.html',
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

    svg = sanitize_svg_for_html(svg)

    generated_hash = hashlib.sha256(svg.encode('utf-8')).hexdigest()

    reference_path = os.path.join(os.path.dirname(__file__), 'reference_alice_qr.svg')
    with open(reference_path, 'r', encoding='utf-8') as f:
        reference_svg = f.read()
    reference_hash = hashlib.sha256(reference_svg.encode('utf-8')).hexdigest()

    assert generated_hash == reference_hash, (
        f'Generated QR hash {generated_hash} does not match reference {reference_hash}'
    )

    assert svg == reference_svg, 'Generated SVG content does not match reference.'
