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
    # should contain the inserted decoration group when decoration is enabled
    assert '<svg' in svg
    assert re.search(
        r'<g[^>]+id=["\']xmas-decoration["\']', svg
    ), 'Expected xmas-decoration group when decorate=True'
    # data attribute should still be present and match the requested color
    assert re.search(
        r'data-qr-default-foreground-color=["\']#001122["\']', svg
    )


def test_decoration_types():
    """Test that all decoration types can be generated without errors."""
    decoration_types = ['tree', 'snowman', 'santa', 'gift', 'star', 'candy-cane', 'bell']

    for deco_type in decoration_types:
        svg = generate_svg(
            f'https://example.com/test-{deco_type}',
            foreground_color='#0b6623',
            background_color='#ffffff',
            decorate=True,
            decoration_type=deco_type,
        )
        assert '<svg' in svg, f'Missing <svg> tag for {deco_type}'
        assert re.search(
            r'<g[^>]+id=["\']xmas-decoration["\']', svg
        ), f'Missing xmas-decoration group for {deco_type}'
        # Verify SVG is substantial (not empty decoration)
        assert len(svg) > 500, f'SVG too small for {deco_type}'


def test_tree_styles():
    """Test that tree decoration supports fancy and plain styles."""
    for style in ['fancy', 'plain']:
        svg = generate_svg(
            f'https://example.com/test-tree-{style}',
            foreground_color='#0b6623',
            background_color='#ffffff',
            decorate=True,
            decoration_type='tree',
            tree_style=style,
        )
        assert '<svg' in svg, f'Missing <svg> tag for tree-{style}'
        assert re.search(
            r'<g[^>]+id=["\']xmas-decoration["\']', svg
        ), f'Missing decoration group for tree-{style}'

        if style == 'fancy':
            # Fancy tree should have baubles/ornaments
            assert 'bauble' in svg.lower() or 'fill="#b71c1c"' in svg, \
                'Fancy tree should have decorative elements'
        # Both styles should have the green foliage
        assert '#0b6623' in svg, f'Tree should have green color in {style} style'


def test_snowman_decoration_content():
    """Test that snowman decoration contains expected elements."""
    svg = generate_svg(
        'https://example.com/test-snowman',
        decorate=True,
        decoration_type='snowman',
    )
    # Snowman should have circles for snowballs
    assert 'circle' in svg.lower(), 'Snowman should contain circles'
    # Snowman should have white fill for snow
    assert '#ffffff' in svg.lower() or 'white' in svg.lower(), \
        'Snowman should have white elements'


def test_santa_decoration_content():
    """Test that Santa decoration contains expected elements."""
    svg = generate_svg(
        'https://example.com/test-santa',
        decorate=True,
        decoration_type='santa',
    )
    # Santa should have red hat
    assert '#b71c1c' in svg or 'red' in svg.lower(), 'Santa should have red hat'
    # Santa should have face/skin tone
    assert 'fill="#fdd0b5"' in svg or 'face' in svg.lower(), 'Santa should have face'


def test_default_decoration_is_tree():
    """Test that default decoration type is tree with fancy style."""
    svg = generate_svg(
        'https://example.com/test-default',
        decorate=True,
    )
    # Should contain tree elements (green foliage)
    assert '#0b6623' in svg, 'Default should be tree with green color'
    # Should be fancy style by default (has decorations)
    assert 'bauble' in svg.lower() or '#b71c1c' in svg or '#ffd54a' in svg, \
        'Default tree should be fancy style with decorations'


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
        tree_style='fancy',              # --tree-style default
        decoration_type='tree'           # --decoration-type default
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
