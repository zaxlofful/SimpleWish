"""Security tests for generate_recipient.py and generate_qr_svg.py.

These tests verify that:
1.  CSS injection via the ``accent``/``muted`` fields is blocked.
2.  ``javascript:`` and ``data:`` URL injection in gift ``href`` fields is
    blocked and the item falls back to plain text.
3.  SVG ``<script>`` tags and inline event handlers are stripped by
    ``sanitize_svg_for_html``.
"""
from pathlib import Path

from scripts.generate_recipient import (
    render_from_template,
    _is_safe_css_color,
    _is_safe_href,
)
from scripts.generate_qr_svg import sanitize_svg_for_html


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_template() -> str:
    repo_root = Path(__file__).resolve().parent.parent
    return (repo_root / 'index.html').read_text(encoding='utf-8')


# ---------------------------------------------------------------------------
# _is_safe_css_color
# ---------------------------------------------------------------------------

class TestIsSafeCssColor:
    def test_hex_3(self):
        assert _is_safe_css_color('#abc')

    def test_hex_6(self):
        assert _is_safe_css_color('#1565C0')

    def test_hex_8(self):
        assert _is_safe_css_color('#1565C0ff')

    def test_rgb(self):
        assert _is_safe_css_color('rgb(21, 101, 192)')

    def test_rgba(self):
        assert _is_safe_css_color('rgba(21, 101, 192, 0.5)')

    def test_hsl(self):
        assert _is_safe_css_color('hsl(212, 80%, 42%)')

    def test_named_color(self):
        assert _is_safe_css_color('red')
        assert _is_safe_css_color('cornflowerblue')

    def test_injection_closes_block(self):
        assert not _is_safe_css_color('red; } body { display:none }')

    def test_injection_url(self):
        assert not _is_safe_css_color('red; background: url(https://evil.com/)')

    def test_injection_expression(self):
        assert not _is_safe_css_color('expression(alert(1))')

    def test_empty_string(self):
        assert not _is_safe_css_color('')

    def test_semicolon_only(self):
        assert not _is_safe_css_color(';')

    def test_leading_trailing_whitespace(self):
        # whitespace should be stripped before matching
        assert _is_safe_css_color('  #aabbcc  ')


# ---------------------------------------------------------------------------
# _is_safe_href
# ---------------------------------------------------------------------------

class TestIsSafeHref:
    def test_https(self):
        assert _is_safe_href('https://example.com/item')

    def test_http(self):
        assert _is_safe_href('http://example.com/item')

    def test_mailto(self):
        assert _is_safe_href('mailto:user@example.com')

    def test_javascript_protocol(self):
        assert not _is_safe_href('javascript:alert(1)')

    def test_javascript_mixed_case(self):
        assert not _is_safe_href('JaVaScRiPt:alert(1)')

    def test_data_uri(self):
        assert not _is_safe_href('data:text/html,<script>alert(1)</script>')

    def test_vbscript(self):
        assert not _is_safe_href('vbscript:msgbox(1)')

    def test_empty(self):
        assert not _is_safe_href('')

    def test_relative_url(self):
        # Relative URLs without explicit scheme are disallowed
        assert not _is_safe_href('/relative/path')

    def test_protocol_relative(self):
        # Protocol-relative URLs are disallowed (ambiguous)
        assert not _is_safe_href('//example.com/item')


# ---------------------------------------------------------------------------
# CSS injection via render_from_template
# ---------------------------------------------------------------------------

class TestCSSInjection:
    """Verify that malicious accent/muted values are not injected into CSS."""

    def test_css_injection_accent_breaks_block(self):
        """A closing brace in accent must NOT appear in the rendered output."""
        tmpl = _load_template()
        data = {'accent': 'red; } body { display: none }'}
        rendered = render_from_template(tmpl, data)
        # The malicious payload must not be present
        assert 'display: none' not in rendered
        # The original --accent default should remain unchanged
        assert '--accent:' in rendered

    def test_css_injection_accent_url(self):
        tmpl = _load_template()
        data = {'accent': '#fff; background: url(https://evil.com/)'}
        rendered = render_from_template(tmpl, data)
        assert 'evil.com' not in rendered

    def test_css_injection_muted_expression(self):
        tmpl = _load_template()
        data = {'muted': 'expression(alert(1))'}
        rendered = render_from_template(tmpl, data)
        assert 'expression' not in rendered

    def test_valid_hex_accent_is_applied(self):
        tmpl = _load_template()
        data = {'accent': '#1565C0'}
        rendered = render_from_template(tmpl, data)
        assert '--accent:#1565C0;' in rendered

    def test_valid_rgb_accent_is_applied(self):
        tmpl = _load_template()
        data = {'accent': 'rgb(21, 101, 192)'}
        rendered = render_from_template(tmpl, data)
        assert '--accent:rgb(21, 101, 192);' in rendered

    def test_valid_named_muted_is_applied(self):
        tmpl = _load_template()
        data = {'muted': 'gray'}
        rendered = render_from_template(tmpl, data)
        assert '--muted:gray;' in rendered


# ---------------------------------------------------------------------------
# javascript: URL injection via gift href
# ---------------------------------------------------------------------------

class TestJavascriptUrlInjection:
    """Verify that javascript: / data: hrefs are rendered as plain text."""

    def test_javascript_href_not_in_anchor(self):
        tmpl = _load_template()
        data = {
            'gifts': [
                {'text': 'Click me', 'href': 'javascript:alert(1)'},
            ]
        }
        rendered = render_from_template(tmpl, data)
        # Should NOT contain a link with the javascript: href
        assert 'href="javascript:' not in rendered
        assert "href='javascript:" not in rendered
        # The visible text should still appear
        assert 'Click me' in rendered

    def test_javascript_href_mixed_case(self):
        tmpl = _load_template()
        data = {'gifts': [{'text': 'Boom', 'href': 'JaVaScRiPt:alert(1)'}]}
        rendered = render_from_template(tmpl, data)
        assert 'href="JaVaScRiPt:' not in rendered
        assert 'Boom' in rendered

    def test_data_uri_href_not_in_anchor(self):
        tmpl = _load_template()
        data = {
            'gifts': [
                {'text': 'Evil', 'href': 'data:text/html,<script>alert(1)</script>'},
            ]
        }
        rendered = render_from_template(tmpl, data)
        # The malicious data: href must not appear as an anchor href
        # (the favicon <link href="data:..."> is unrelated and fine)
        assert '<a href="data:' not in rendered
        assert 'Evil' in rendered

    def test_vbscript_href_not_in_anchor(self):
        tmpl = _load_template()
        data = {'gifts': [{'text': 'VB', 'href': 'vbscript:msgbox(1)'}]}
        rendered = render_from_template(tmpl, data)
        assert 'href="vbscript:' not in rendered

    def test_https_href_is_allowed(self):
        tmpl = _load_template()
        data = {
            'gifts': [
                {'text': 'Safe link', 'href': 'https://example.com/product'},
            ]
        }
        rendered = render_from_template(tmpl, data)
        assert 'href="https://example.com/product"' in rendered
        assert 'Safe link' in rendered

    def test_http_href_is_allowed(self):
        tmpl = _load_template()
        data = {
            'gifts': [
                {'text': 'HTTP link', 'href': 'http://example.com/product'},
            ]
        }
        rendered = render_from_template(tmpl, data)
        assert 'href="http://example.com/product"' in rendered


# ---------------------------------------------------------------------------
# SVG script injection via sanitize_svg_for_html
# ---------------------------------------------------------------------------

class TestSvgScriptInjection:
    """Verify that <script> tags and on* event handlers are stripped from SVG."""

    def test_script_tag_removed(self):
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
            '<script>alert("xss")</script>'
            '<circle cx="50" cy="50" r="40"/>'
            '</svg>'
        )
        result = sanitize_svg_for_html(svg, pretty=False)
        assert '<script' not in result
        assert 'alert(' not in result
        assert '<circle' in result

    def test_script_tag_with_type_removed(self):
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<script type="text/javascript">evil()</script>'
            '</svg>'
        )
        result = sanitize_svg_for_html(svg, pretty=False)
        assert '<script' not in result
        assert 'evil()' not in result

    def test_self_closing_script_removed(self):
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><script src="//evil.com/x.js"/></svg>'
        result = sanitize_svg_for_html(svg, pretty=False)
        assert '<script' not in result

    def test_onload_event_handler_removed(self):
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)">'
            '<circle cx="50" cy="50" r="40"/>'
            '</svg>'
        )
        result = sanitize_svg_for_html(svg, pretty=False)
        assert 'onload' not in result
        assert 'alert(1)' not in result

    def test_onclick_event_handler_removed(self):
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<circle cx="50" cy="50" r="40" onclick="steal()"/>'
            '</svg>'
        )
        result = sanitize_svg_for_html(svg, pretty=False)
        assert 'onclick' not in result

    def test_onerror_event_handler_removed(self):
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<image href="x" onerror="alert(1)"/>'
            '</svg>'
        )
        result = sanitize_svg_for_html(svg, pretty=False)
        assert 'onerror' not in result

    def test_style_block_removed(self):
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<style>body { display: none }</style>'
            '<rect width="100" height="100"/>'
            '</svg>'
        )
        result = sanitize_svg_for_html(svg, pretty=False)
        assert '<style' not in result
        assert 'display: none' not in result
        # The rect element should remain
        assert '<rect' in result

    def test_clean_svg_passes_through(self):
        """A clean SVG with no scripts or handlers must not be altered."""
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="250" height="250">'
            '<circle cx="125" cy="125" r="100" fill="#0b6623"/>'
            '</svg>'
        )
        result = sanitize_svg_for_html(svg, pretty=False)
        assert '<circle' in result
        assert 'fill="#0b6623"' in result

    def test_xml_prolog_removed(self):
        svg = '<?xml version="1.0" encoding="utf-8"?><svg><rect/></svg>'
        result = sanitize_svg_for_html(svg, pretty=False)
        assert '<?xml' not in result
        assert '<rect' in result

    def test_doctype_removed(self):
        svg = '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "">\n<svg><rect/></svg>'
        result = sanitize_svg_for_html(svg, pretty=False)
        assert '<!DOCTYPE' not in result
        assert '<rect' in result

    def test_multiline_script_removed(self):
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">\n'
            '<script>\n'
            '  var x = 1;\n'
            '  alert(x);\n'
            '</script>\n'
            '<rect/>\n'
            '</svg>'
        )
        result = sanitize_svg_for_html(svg, pretty=False)
        assert '<script' not in result
        assert 'alert(' not in result
        assert '<rect' in result

    def test_script_injection_in_pretty_mode(self):
        """Ensure script removal also works in pretty-print mode."""
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
            '<script>alert("xss")</script>'
            '<circle cx="5" cy="5" r="4"/>'
            '</svg>'
        )
        result = sanitize_svg_for_html(svg, pretty=True)
        assert '<script' not in result
        assert 'alert(' not in result
        assert 'circle' in result
