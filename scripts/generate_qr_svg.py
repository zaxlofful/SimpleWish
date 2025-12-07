#!/usr/bin/env python3
"""
Generate per-file SVG QR images and write them to an output directory.

Usage:
    python scripts/generate_qr_svg.py --root-domain "https://example.com" --pattern "*.html" --out-dir scripts/generated_qr

This script produces one SVG per input HTML file named <basename>.svg (basename without extension).

Notes on recent refactor:
- The CLI and per-page meta keys use `foreground`/`background` instead of the older dark/light names.
- The `--transparent` option was removed; transparency handling was unfinished and is no longer supported.
- Reserve options are unified in `--reserve` which encodes mode+position (e.g. "overlay-bottom-right", "quietzone").
"""
import argparse
import glob
import os
import re
import urllib.parse
import segno


def read_meta_tags_from_html(path: str):
    """Return a dict of meta tag name->content for qr-foreground, qr-background, qr-decorate if present."""
    res = {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return res
    # Remove HTML comments first so commented example meta tags don't get picked up
    content_no_comments = re.sub(r'<!--.*?-->', '', content, flags=re.S)

    # naive regex to find <meta name="..." content="..."> in uncommented content
    for m in re.finditer(r"<meta\s+name=[\"']([^\"']+)[\"']\s+content=[\"']([^\"']+)[\"']", content_no_comments, flags=re.I):
        name = m.group(1).strip()
        val = m.group(2).strip()
        # collect known per-page QR metadata. Add new keys here as the generator grows.
        if name in (
            'qr-foreground-color',
            'qr-background-color',
            'qr-decorate',
            'qr-tree-style',
        ):
            res[name] = val
    return res


def clean_filename_to_path(filename: str) -> str:
    return urllib.parse.quote(filename)


def generate_svg(url: str, foreground_color: str = '#0b6623', background_color: str = '#ffffff', decorate: bool = True, border: int = 8, reserve_mode: str = 'overlay', logo_pos: str = 'bottom-right', logo_size_pct: float = 20.0, ecc: str = 'H', tree_style: str = 'fancy') -> str:
    """Generate an embeddable SVG string for the given URL with optional decoration.

    The SVG returned is safe to inline into HTML (no prolog/doctype) and will have
    width/height set to 250 and a viewBox inserted if missing.
    """
    # Create QR with requested error correction level.
    qr = segno.make(url, micro=False, error=ecc)
    svg = qr.svg_inline(dark=foreground_color, light=background_color, border=border)

    # Replace black fills with currentColor so CSS can recolor the QR
    svg = re.sub(r'(?i)fill=["\']\s*rgb\(\s*0\s*,\s*0\s*,\s*0\s*\)\s*["\']', 'fill="currentColor"', svg)
    svg = re.sub(r'(?i)fill=["\']\s*#0{3,6}\s*["\']', 'fill="currentColor"', svg)

    # Replace fill declarations inside style attributes
    def _fix_style(m):
        s = m.group(1)
        s = re.sub(r'(?i)fill\s*:\s*rgb\(\s*0\s*,\s*0\s*,\s*0\s*\)', 'fill:currentColor', s)
        s = re.sub(r'(?i)fill\s*:\s*#0{3,6}', 'fill:currentColor', s)
        return f'style="{s}"'

    svg = re.sub(r'(?i)style\s*=\s*"([^"]*)"', _fix_style, svg)

    # Ensure the root <svg> has a helpful class and a data attribute with the default foreground color
    def _add_data_attr(m):
        tag = m.group(1)
        attrs = m.group(2) or ''
        if re.search(r'\bclass\s*=\s*"', attrs) is None:
            attrs += ' class="qr-svg"'
        # expose the default foreground color so CSS can override via currentColor
        if re.search(r'\bdata-qr-default-foreground-color\s*=\s*"', attrs) is None:
            attrs += f' data-qr-default-foreground-color="{foreground_color}"'
        return f'{tag}{attrs}'

    svg = re.sub(r'(<svg\b)([^>]*)', _add_data_attr, svg, count=1)

    # Determine internal SVG coordinate system (viewBox or width/height)
    vb_w = vb_h = None
    m = re.search(r'viewBox="0 0 (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)"', svg)
    if m:
        vb_w = float(m.group(1))
        vb_h = float(m.group(2))
    else:
        m2 = re.search(r'width="(\d+(?:\.\d+)?)"\s+height="(\d+(?:\.\d+)?)"', svg)
        if m2:
            vb_w = float(m2.group(1))
            vb_h = float(m2.group(2))

    if vb_w is None or vb_h is None:
        vb_w = vb_h = 250.0

    # Default decorative tree size (reference coordinates are 200x200)
    tree_width = vb_w * 0.46
    tree_height = vb_h * 0.46

    # Default quietzone placement: centered along bottom with a small margin
    margin = vb_h * 0.02
    q_tx = (vb_w - tree_width) / 2.0
    q_ty = vb_h - tree_height - margin

    # Two tree styles: 'fancy' (default, with star, garlands, baubles) and 'plain' (only green polygons)
    fancy_inner = '''
    <g>
        <!-- layered green foliage -->
        <polygon points="50,185 100,115 150,185" fill="#0b6623" />
        <polygon points="60,155 100,95 140,155" fill="#0b6623" />
        <polygon points="70,130 100,70 130,130" fill="#0b6623" />
            <!-- decorative star (~20% smaller than before) -->
            <polygon points="100,54.11 105.04,67.07 118.72,67.07 108.64,75.71 113.68,88.67 100,80.03 86.32,88.67 91.36,75.71 81.28,67.07 94.96,67.07" fill="#ffd54a" />
            <!-- garland (shorter, lower ribbon) -->
            <path d="M74,128 C84,117 116,117 126,128" fill="none" stroke="#8fbf5f" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" opacity="0.95" />
            <path d="M64,155 C80,142 120,142 136,155" fill="none" stroke="#6aa144" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" opacity="0.95" />
            <!-- baubles with subtle stroke and highlight -->
            <g stroke="#8b0000" stroke-width="0.8">
            <ellipse cx="92" cy="98" rx="4" ry="4.6" fill="#b71c1c" />
            <circle cx="118" cy="118" r="3.6" fill="#b71c1c" />
            </g>
            <g stroke="#b58a00" stroke-width="0.6">
            <circle cx="76" cy="126" r="3.2" fill="#ffd54a" />
            <circle cx="128" cy="138" r="2.8" fill="#fff176" />
            </g>
                <!-- small blue baubles -->
                <circle cx="106" cy="112" r="2.6" fill="#1976D2" />
                <circle cx="84" cy="140" r="2.2" fill="#2196F3" />
            <!-- tiny lights (glossy dots) -->
            <circle cx="104" cy="92" r="1.8" fill="#ffffff" opacity="0.95" />
            <circle cx="88" cy="118" r="1.6" fill="#fff8e1" opacity="0.95" />
            <circle cx="112" cy="142" r="1.6" fill="#ffe082" opacity="0.95" />
                <!-- more visible bow: loops, tails, knot and highlight -->
                <g id="xmas-bow" transform="translate(0,0)" aria-hidden="true">
                <!-- left loop -->
                <path d="M92,158 C86,150 88,142 96,150 C100,154 96,158 92,158" fill="#e53935" stroke="#7b1f1f" stroke-width="0.7" />
                <!-- right loop -->
                <path d="M108,158 C114,150 112,142 104,150 C100,154 104,158 108,158" fill="#e53935" stroke="#7b1f1f" stroke-width="0.7" />
                <!-- left tail -->
                <path d="M96,162 C92,168 84,174 78,180" fill="none" stroke="#c62828" stroke-width="2" stroke-linecap="round" />
                <!-- right tail -->
                <path d="M104,162 C108,168 116,174 122,180" fill="none" stroke="#c62828" stroke-width="2" stroke-linecap="round" />
                <!-- knot -->
                <circle cx="100" cy="156" r="2.6" fill="#7b1f1f" />
                <!-- tiny highlight on knot -->
                <circle cx="101" cy="155.2" r="0.7" fill="#fff8e1" opacity="0.9" />
                </g>
            <!-- decorative gloss spots on larger baubles -->
            <circle cx="116" cy="116" r="0.9" fill="#ffffff" opacity="0.9" />
            <circle cx="92" cy="96" r="0.8" fill="#ffffff" opacity="0.9" />
        <!-- trunk removed to simplify the decoration -->
    </g>
'''

    plain_inner = '''
    <g>
        <!-- plain layered green foliage (no decorations) -->
        <polygon points="50,185 100,115 150,185" fill="#0b6623" />
        <polygon points="60,155 100,95 140,155" fill="#0b6623" />
        <polygon points="70,130 100,70 130,130" fill="#0b6623" />
    </g>
'''

        chosen_inner = fancy_inner if tree_style == 'fancy' else plain_inner

        quiet_tree_group = f'''
    <g id="xmas-tree" transform="translate({q_tx:.2f}, {q_ty:.2f}) scale({tree_width/200.0:.6f})" aria-hidden="true">
{chosen_inner}
    </g>
'''

    # If reserve_mode is overlay, compute placement based on reserved rect and allow an overlay multiplier and shift
    tree_group = quiet_tree_group
    if reserve_mode == 'overlay':
        rect_w = vb_w * (logo_size_pct / 100.0)
        rect_h = vb_h * (logo_size_pct / 100.0)
        padding = vb_w * 0.01
        if logo_pos == 'bottom-right':
            rect_x = vb_w - rect_w - padding
            rect_y = vb_h - rect_h - padding
        elif logo_pos == 'bottom-left':
            rect_x = padding
            rect_y = vb_h - rect_h - padding
        elif logo_pos == 'top-left':
            rect_x = padding
            rect_y = padding
        elif logo_pos == 'top-right':
            rect_x = vb_w - rect_w - padding
            rect_y = padding
        else:
            rect_x = (vb_w - rect_w) / 2.0
            rect_y = (vb_h - rect_h) / 2.0

        overlay_multiplier = float(globals().get('__overlay_multiplier__', 1.15))
        desired_w = rect_w * overlay_multiplier
        desired_h = rect_h * overlay_multiplier
        scale = desired_w / 200.0

        # Anchor tree so its bottom-right lines up with rect's bottom-right for bottom-right position
        tx = rect_x + rect_w - desired_w
        ty = rect_y + rect_h - desired_h

        # apply horizontal shift (positive moves right)
        overlay_shift_x = float(globals().get('__overlay_shift_x__', 0.0))
        tx = tx + (rect_w * overlay_shift_x)
        # apply vertical shift (positive moves down)
        overlay_shift_y = float(globals().get('__overlay_shift_y__', 0.0))
        ty = ty + (rect_h * overlay_shift_y)

    # Build overlay variant using the chosen inner content
        tree_group = f'''
    <g id="xmas-tree" transform="translate({tx:.2f}, {ty:.2f}) scale({scale:.6f})" aria-hidden="true">
{chosen_inner}
    </g>
'''

    # Insert the tree_group before the closing </svg> only when decoration is enabled
    if decorate and svg.strip().endswith('</svg>'):
        svg = svg.rstrip()[:-6] + '\n' + tree_group + '</svg>'

    # Ensure the generated SVG root renders at 250x250 pixels
    def set_size(m):
        tag = m.group(1)
        attrs = m.group(2) or ''
        attrs = re.sub(r'\swidth\s*=\s*"[^"]*"', '', attrs)
        attrs = re.sub(r'\sheight\s*=\s*"[^"]*"', '', attrs)
        return f'{tag}{attrs} width="250" height="250"'

    svg = re.sub(r'(<svg\b)([^>]*)', set_size, svg, count=1)

    # Add viewBox if missing
    if re.search(r'viewBox\s*=\s*"', svg) is None:
        try:
            vw = int(round(vb_w))
            vh = int(round(vb_h))
        except Exception:
            vw, vh = 250, 250

        def add_vb(m):
            tag = m.group(1)
            attrs = m.group(2) or ''
            return f'{tag}{attrs} viewBox="0 0 {vw} {vh}"'

        svg = re.sub(r'(<svg\b)([^>]*)', add_vb, svg, count=1)

    return svg


def sanitize_svg_for_html(svg: str) -> str:
    """Strip XML prolog and DOCTYPE so the SVG is safe to embed directly in HTML."""
    # remove XML prolog like <?xml version="1.0" encoding="utf-8"?>
    svg = re.sub(r'^\s*<\?xml[^>]*>\s*', '', svg)
    # remove DOCTYPE declarations
    svg = re.sub(r'<!DOCTYPE[^>]*>\s*', '', svg, flags=re.I)
    return svg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root-domain', required=True)
    parser.add_argument('--pattern', default='*.html')
    parser.add_argument('--out-dir', default='scripts/generated_qr')
    parser.add_argument('--foreground-color', dest='foreground_color', default='#0b6623', help='Foreground color for QR modules')
    parser.add_argument('--background-color', dest='background_color', default='#ffffff', help='Background color for QR')
    parser.add_argument('--no-decorate', dest='decorate', action='store_false', default=True, help='Disable decorative tree (opt-out)')
    # Decoration is opt-out via --no-decorate; when decorating we reserve a bottom-right overlay by default.
    parser.add_argument('--logo-size', type=float, default=20.0, help='Percentage size for reserved logo area (percent of SVG width)')
    parser.add_argument('--overlay-mult', type=float, default=3.0, help='Multiplier to make overlayed tree slightly larger than reserved rect')
    parser.add_argument('--overlay-shift-x', type=float, default=0.90, help='Horizontal shift for overlay tree as fraction of reserved rect width (positive shifts right)')
    parser.add_argument('--overlay-shift-y', type=float, default=0.50, help='Vertical shift for overlay tree as fraction of reserved rect height (positive shifts down)')
    parser.add_argument('--ecc', choices=['L','M','Q','H'], default='H', help='Error correction level to use when generating QR (higher required for reserve modes)')
    parser.add_argument('--tree-style', choices=['fancy','plain'], default='fancy', help='Style of tree to render: fancy (default) or plain (no decorations)')
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    files = glob.glob(args.pattern)
    if not files:
        print('No files found matching pattern')
        return 0

    for path in files:
        basename = os.path.splitext(os.path.basename(path))[0]
        public_url = urllib.parse.urljoin(args.root_domain.rstrip('/') + '/', urllib.parse.quote(os.path.basename(path)))

        # Read per-file meta tags to override color/decorate if provided
        meta = read_meta_tags_from_html(path)
        # Use per-page meta keys if present, otherwise use CLI defaults
        foreground = meta.get('qr-foreground-color', args.foreground_color)
        background = meta.get('qr-background-color', args.background_color)
        decorate = args.decorate
        if 'qr-decorate' in meta:
            decorate = meta.get('qr-decorate', 'true').lower() in ('1', 'true', 'yes')
        # Per-page override for tree style (fancy or plain)
        tree_style = args.tree_style
        if 'qr-tree-style' in meta:
            v = meta.get('qr-tree-style', '').strip().lower()
            if v in ('fancy', 'plain'):
                tree_style = v
            else:
                # ignore invalid values and leave as CLI/default
                pass

        # Decide reserve behavior: this project places the decorative tree/logo in the
        # bottom-right by default when decoration is enabled. Decoration is opt-out via --no-decorate.
        if decorate:
            reserve_mode = 'overlay'
            logo_pos = 'bottom-right'
        else:
            reserve_mode = None
            logo_pos = 'center'

        # If using overlay, render QR with no border so it fills the viewBox entirely
        border = 0 if reserve_mode == 'overlay' else 8
        # expose overlay multiplier & horizontal/vertical shift globally for the generator (quick way to pass through)
        globals()['__overlay_multiplier__'] = args.overlay_mult
        globals()['__overlay_shift_x__'] = args.overlay_shift_x
        globals()['__overlay_shift_y__'] = args.overlay_shift_y

        svg = generate_svg(public_url, foreground_color=foreground, background_color=background, decorate=decorate, border=border, reserve_mode=reserve_mode, logo_pos=logo_pos, logo_size_pct=args.logo_size, ecc=args.ecc, tree_style=tree_style)

        out_path = os.path.join(args.out_dir, f'{basename}.svg')
        svg = sanitize_svg_for_html(svg)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(svg)
        print(f'Generated {out_path} for {public_url}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
