import sys

import scripts.generate_qr_svg as gen_module
from scripts.generate_qr_svg import generate_svg, sanitize_svg_for_html


def test_sanitize_pretty_indent_2():
    svg = generate_svg('https://example.com/test', decorate=True)
    pretty = sanitize_svg_for_html(svg, pretty=True, indent_spaces=2)
    # should contain lines indented with 2 spaces
    assert '\n  <' in pretty


def test_sanitize_pretty_indent_4():
    svg = generate_svg('https://example.com/test', decorate=True)
    pretty = sanitize_svg_for_html(svg, pretty=True, indent_spaces=4)
    # should contain lines indented with 4 spaces
    assert '\n    <' in pretty


def test_sanitize_minify():
    svg = generate_svg('https://example.com/test', decorate=True)
    compact = sanitize_svg_for_html(svg, pretty=False)
    # compact output should not contain the pretty indent sequences
    assert '\n  <' not in compact and '\n    <' not in compact


def test_cli_minify_writes_compact(tmp_path, monkeypatch):
    # Run the CLI with --minify to write compact SVGs into tmp_path
    outdir = tmp_path / 'out'
    outdir.mkdir()
    argv = [
        'generate_qr_svg.py',
        '--pattern', 'index.html',
        '--out-dir', str(outdir),
        '--minify',
    ]
    monkeypatch.setattr(sys, 'argv', argv)
    # Ensure overlay globals are set to defaults used in tests
    gen_module.__overlay_multiplier__ = 3.0
    gen_module.__overlay_shift_x__ = 0.90
    gen_module.__overlay_shift_y__ = 0.50
    # Run main()
    rc = gen_module.main()
    assert rc == 0
    # Check that the generated file exists and is compact
    generated = outdir / 'index.svg'
    assert generated.exists()
    content = generated.read_text(encoding='utf-8')
    assert '\n  <' not in content and '\n    <' not in content
