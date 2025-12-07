import re

from scripts.generate_qr_svg import generate_svg


def test_generate_svg_basic():
    svg = generate_svg('https://example.com/test', foreground_color='#112233', background_color='#ffffff', decorate=False)
    assert isinstance(svg, str)
    assert '<svg' in svg
    # ensure the data attribute for default foreground color exists (allow single or double quotes)
    assert re.search(r'data-qr-default-foreground-color=["\']#112233["\']', svg)


def test_generate_svg_with_decoration():
    svg = generate_svg('https://example.com/test-decorate', foreground_color='#001122', background_color='#ffffff', decorate=True)
    # should contain the inserted tree group when decoration is enabled
    assert '<svg' in svg
    assert re.search(r'<g[^>]+id=["\']xmas-tree["\']', svg), 'Expected xmas-tree group when decorate=True'
    # data attribute should still be present and match the requested color
    assert re.search(r'data-qr-default-foreground-color=["\']#001122["\']', svg)


def test_viewbox_and_size():
    svg = generate_svg('https://example.com/size-test', foreground_color='#334455', background_color='#ffffff', decorate=False)
    # viewBox should exist and width/height should be set to 250
    assert re.search(r'viewBox="0 0 \d+ \d+"', svg), 'Expected a viewBox attribute on the generated SVG'
    assert re.search(r'width="250"\s+height="250"', svg) or re.search(r'height="250"\s+width="250"', svg)


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
