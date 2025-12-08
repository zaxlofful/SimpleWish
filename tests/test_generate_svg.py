import hashlib
import os
import re

from scripts.generate_qr_svg import generate_svg


def test_generate_svg_basic():
    svg = generate_svg(
        'https://example.com/test',
        foreground_color='#112233',
        background_color='#ffffff',
        decorate=False,
    )
    assert isinstance(svg, str)
    assert '<svg' in svg
    # ensure the data attribute for default foreground color exists
    # (allow single or double quotes)
    assert re.search(
        r'data-qr-default-foreground-color=["\']#112233["\']', svg
    )


def test_generate_svg_with_decoration():
    svg = generate_svg(
        'https://example.com/test-decorate',
        foreground_color='#001122',
        background_color='#ffffff',
        decorate=True,
    )
    # should contain the inserted tree group when decoration is enabled
    assert '<svg' in svg
    assert re.search(
        r'<g[^>]+id=["\']xmas-tree["\']', svg
    ), 'Expected xmas-tree group when decorate=True'
    # data attribute should still be present and match the requested color
    assert re.search(
        r'data-qr-default-foreground-color=["\']#001122["\']', svg
    )


def test_viewbox_and_size():
    svg = generate_svg(
        'https://example.com/size-test',
        foreground_color='#334455',
        background_color='#ffffff',
        decorate=False,
    )
    # viewBox should exist and width/height should be set to 250
    assert re.search(
        r'viewBox="0 0 \d+ \d+"', svg
    ), 'Expected a viewBox attribute on the generated SVG'
    a = re.search(r'width="250"\s+height="250"', svg)
    b = re.search(r'height="250"\s+width="250"', svg)
    assert (a or b)


def test_read_meta_tags_from_html(tmp_path):
    from scripts.generate_qr_svg import read_meta_tags_from_html
    html = (
        '<!doctype html>\n<html><head>'
        '<meta name="qr-foreground-color" content="#abc123">'
        '<meta name="qr-background-color" content="#ffffff">'
        '<meta name="qr-decorate" content="false">'
        '</head><body></body></html>'
    )
    p = tmp_path / 'sample.html'
    p.write_text(html, encoding='utf-8')
    meta = read_meta_tags_from_html(str(p))
    assert meta.get('qr-foreground') is None
    assert meta.get('qr-foreground-color') == '#abc123'
    assert meta.get('qr-background-color') == '#ffffff'
    assert meta.get('qr-decorate') == 'false'


def test_qr_generation_matches_reference():
    """Test that QR generation with default settings produces consistent output.
    
    This test generates a QR code with default settings (matching the command:
    python scripts/generate_qr_svg.py --root-domain "https://example.com" 
    --pattern "index.html" --out-dir scripts/generated_qr) and compares its 
    hash to a reference file to ensure the QR generation is deterministic.
    """
    from scripts.generate_qr_svg import sanitize_svg_for_html
    import scripts.generate_qr_svg as gen_module
    
    # Set the global variables that control overlay positioning
    # These match the defaults from argparse (lines 392-415)
    gen_module.__overlay_multiplier__ = 3.0   # --overlay-mult default
    gen_module.__overlay_shift_x__ = 0.90     # --overlay-shift-x default
    gen_module.__overlay_shift_y__ = 0.50     # --overlay-shift-y default
    
    # Generate QR with default CLI settings for index.html
    # These match the defaults from argparse in generate_qr_svg.py
    svg = generate_svg(
        url='https://example.com/index.html',
        foreground_color='#0b6623',      # --foreground-color default
        background_color='#ffffff',      # --background-color default
        decorate=True,                   # decoration is enabled by default
        border=0,                        # border=0 when reserve_mode='overlay'
        logo_size_pct=20.0,             # --logo-size default
        logo_pos='bottom-right',         # default position when decorating
        reserve_mode='overlay',          # default mode when decorating
        ecc='H',                         # --ecc default
        tree_style='fancy'               # --tree-style default
    )
    
    # Apply the same sanitization that the CLI script applies
    svg = sanitize_svg_for_html(svg)
    
    # Calculate hash of generated SVG
    generated_hash = hashlib.sha256(svg.encode('utf-8')).hexdigest()
    
    # Read reference file and calculate its hash
    reference_path = os.path.join(
        os.path.dirname(__file__), 'reference_qr.svg'
    )
    with open(reference_path, 'r', encoding='utf-8') as f:
        reference_svg = f.read()
    reference_hash = hashlib.sha256(reference_svg.encode('utf-8')).hexdigest()
    
    # Hashes should match exactly
    assert generated_hash == reference_hash, (
        f'Generated QR hash {generated_hash} does not match '
        f'reference hash {reference_hash}. '
        'This indicates the QR generation algorithm has changed.'
    )
    
    # Also verify the SVG content is identical
    assert svg == reference_svg, (
        'Generated SVG content does not match reference. '
        'This indicates the QR generation is not deterministic.'
    )

