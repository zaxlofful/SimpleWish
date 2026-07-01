from pathlib import Path
import sys

import pytest

import scripts.inject_qr_svg as inject_module
from scripts.inject_qr_svg import inject, MARKER_START, MARKER_END


def make_html_with_marker(path: Path, leading_ws=''):
    content = (
        f"prefix\n{leading_ws}{MARKER_START}\n{leading_ws}\n{leading_ws}{MARKER_END}\nsuffix\n"
    )
    path.write_text(content, encoding='utf-8')
    return content


def test_inject_basic(tmp_path):
    html = tmp_path / 'sample.html'
    make_html_with_marker(html)

    svg = '<svg>\n<rect/></svg>'

    changed = inject(svg, str(html), preserve_manual=False)
    assert changed is True

    new_content = html.read_text(encoding='utf-8')
    assert '<svg' in new_content
    # ensure injection happened between markers
    assert MARKER_START in new_content and MARKER_END in new_content


def test_inject_preserve_manual(tmp_path):
    html = tmp_path / 'manual.html'
    # create manual content between markers
    content = f"start\n{MARKER_START}\n    MANUAL CONTENT\n{MARKER_END}\nend\n"
    html.write_text(content, encoding='utf-8')

    svg = '<svg></svg>'
    changed = inject(svg, str(html), preserve_manual=True)
    assert changed is False


def test_inject_no_markers(tmp_path):
    html = tmp_path / 'nomarker.html'
    html.write_text('no markers here', encoding='utf-8')
    svg = '<svg></svg>'
    changed = inject(svg, str(html))
    assert changed is False


def test_inject_indentation_tab(tmp_path):
    html = tmp_path / 'tabbed.html'
    # marker line starts with a tab
    make_html_with_marker(html, leading_ws='\t')
    svg = '<svg>\n<g></g>\n</svg>'
    changed = inject(svg, str(html))
    assert changed is True
    new_content = html.read_text(encoding='utf-8')
    # injected lines should start with indentation matching the marker
    # we expect the injected SVG to start on the same indentation as the marker
    assert '\n\t<svg' in new_content


@pytest.mark.parametrize(
    'svg',
    [
        '<svg><script>alert(1)</script></svg>',
        '<svg><foreignObject><div>bad</div></foreignObject></svg>',
        '<svg onload="alert(1)"><rect/></svg>',
        '<svg><rect fill="url(https://evil.example/pixel)"/></svg>',
    ],
)
def test_inject_rejects_active_svg_content(tmp_path, svg):
    html = tmp_path / 'sample.html'
    original = make_html_with_marker(html)

    with pytest.raises(ValueError, match='unsafe SVG'):
        inject(svg, str(html))

    assert html.read_text(encoding='utf-8') == original


def test_cli_injects_only_html_matching_pattern(tmp_path, monkeypatch):
    svg_dir = tmp_path / 'generated'
    svg_dir.mkdir()
    (svg_dir / 'sample.svg').write_text(
        '<svg><rect/></svg>',
        encoding='utf-8',
    )
    root_html = tmp_path / 'sample.html'
    root_original = make_html_with_marker(root_html)
    public_dir = tmp_path / 'public'
    public_dir.mkdir()
    public_html = public_dir / 'sample.html'
    make_html_with_marker(public_html)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        'argv',
        [
            'inject_qr_svg.py',
            '--svg-dir',
            'generated',
            '--pattern',
            'public/*.html',
        ],
    )

    assert inject_module.main() == 0
    assert root_html.read_text(encoding='utf-8') == root_original
    assert '<rect' in public_html.read_text(encoding='utf-8')
