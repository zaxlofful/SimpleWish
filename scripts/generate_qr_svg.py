#!/usr/bin/env python3
"""
Generate per-file SVG QR images and write them to an output directory.

Usage:
        python scripts/generate_qr_svg.py \
                --root-domain "https://example.com" --pattern "*.html" \
                --out-dir scripts/generated_qr

This script produces one SVG per input HTML file named <basename>.svg
(basename without extension).

Notes on recent refactor:
- The CLI and per-page meta keys use `foreground`/`background` instead of
    the older dark/light names.
- The `--transparent` option was removed; transparency handling was
    unfinished and is no longer supported.
- Reserve options are unified in `--reserve` which encodes mode+position
    (e.g. "overlay-bottom-right", "quietzone").
"""
import argparse
import glob
import os
import re
import urllib.parse
import segno


def read_meta_tags_from_html(path: str):
    """Return a mapping of meta tag names to content.

    Only known per-page QR metadata keys are collected. On error an empty
    dict is returned.
    """
    res = {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return res
    # Remove HTML comments first so commented example meta tags don't get
    # picked up
    content_no_comments = re.sub(r'<!--.*?-->', '', content, flags=re.S)

    # naive regex to find <meta name="..." content="..."> in uncommented
    # content
    pattern = (
        r"<meta\s+name=[\"']([^\"']+)[\"']\s+"
        r"content=[\"']([^\"']+)[\"']"
    )
    for m in re.finditer(pattern, content_no_comments, flags=re.I):
        name = m.group(1).strip()
        val = m.group(2).strip()
    # collect known per-page QR metadata. Add new keys here as the
    # generator grows.
        if name in (
            'qr-foreground-color',
            'qr-background-color',
            'qr-decorate',
            'qr-tree-style',
            'qr-decoration-type',
        ):
            res[name] = val
    return res


def clean_filename_to_path(filename: str) -> str:
    return urllib.parse.quote(filename)


def get_tree_decoration(style: str = 'fancy') -> str:
    """Generate Christmas tree decoration SVG (fancy or plain)."""
    if style == 'fancy':
        fancy_parts = [
            '<g>',
            '    <!-- layered green foliage -->',
            '    <polygon points="50,185 100,115 150,185"',
            '        fill="#0b6623" />',
            '    <polygon points="60,155 100,95 140,155"',
            '        fill="#0b6623" />',
            '    <polygon points="70,130 100,70 130,130"',
            '        fill="#0b6623" />',
            '    <!-- decorative star (~20% smaller than before) -->',
            (
                '    <polygon points="100,54.11 105.04,67.07 118.72,67.07 '
                '108.64,75.71 113.68,88.67 100,80.03 86.32,88.67 '
                '91.36,75.71 81.28,67.07 94.96,67.07" fill="#ffd54a" />'
            ),
            '    <!-- garland (shorter, lower ribbon) -->',
            '    <path d="M74,128 C84,117 116,117 126,128"',
            '        fill="none" stroke="#8fbf5f"',
            '        stroke-width="6" stroke-linecap="round"',
            '        stroke-linejoin="round" opacity="0.95" />',
            '    <path d="M64,155 C80,142 120,142 136,155"',
            '        fill="none" stroke="#6aa144"',
            '        stroke-width="4" stroke-linecap="round"',
            '        stroke-linejoin="round" opacity="0.95" />',
            '    <!-- baubles with subtle stroke and highlight -->',
            '    <g stroke="#8b0000" stroke-width="0.8">',
            '    <ellipse cx="92" cy="98" rx="4" ry="4.6"',
            '        fill="#b71c1c" />',
            '    <circle cx="118" cy="118" r="3.6"',
            '        fill="#b71c1c" />',
            '    </g>',
            '    <g stroke="#b58a00" stroke-width="0.6">',
            '    <circle cx="76" cy="126" r="3.2"',
            '        fill="#ffd54a" />',
            '    <circle cx="128" cy="138" r="2.8"',
            '        fill="#fff176" />',
            '    </g>',
            '    <!-- small blue baubles -->',
            '    <circle cx="106" cy="112" r="2.6"',
            '        fill="#1976D2" />',
            '    <circle cx="84" cy="140" r="2.2"',
            '        fill="#2196F3" />',
            '    <!-- tiny lights (glossy dots) -->',
            '    <circle cx="104" cy="92" r="1.8"',
            '        fill="#ffffff" opacity="0.95" />',
            '    <circle cx="88" cy="118" r="1.6"',
            '        fill="#fff8e1" opacity="0.95" />',
            '    <circle cx="112" cy="142" r="1.6"',
            '        fill="#ffe082" opacity="0.95" />',
            '    <!-- more visible bow: loops, tails, knot and highlight -->',
            '    <g id="xmas-bow" transform="translate(0,0)"',
            '        aria-hidden="true">',
            '    <!-- left loop -->',
            '    <path d="M92,158 C86,150 88,142 96,150 '
            'C100,154 96,158 92,158"',
            '        fill="#e53935" stroke="#7b1f1f"',
            '        stroke-width="0.7" />',
            '    <!-- right loop -->',
            '    <path d="M108,158 C114,150 112,142 104,150 '
            'C100,154 104,158 108,158"',
            '        fill="#e53935" stroke="#7b1f1f"',
            '        stroke-width="0.7" />',
            '    <!-- left tail -->',
            '    <path d="M96,162 C92,168 84,174 78,180"',
            '        fill="none" stroke="#c62828"',
            '        stroke-width="2" stroke-linecap="round" />',
            '    <!-- right tail -->',
            '    <path d="M104,162 C108,168 116,174 122,180"',
            '        fill="none" stroke="#c62828"',
            '        stroke-width="2" stroke-linecap="round" />',
            '    <!-- knot -->',
            '    <circle cx="100" cy="156" r="2.6"',
            '        fill="#7b1f1f" />',
            '    <!-- tiny highlight on knot -->',
            '    <circle cx="101" cy="155.2" r="0.7"',
            '        fill="#fff8e1" opacity="0.9" />',
            '    </g>',
            '    <!-- decorative gloss spots on larger baubles -->',
            '    <circle cx="116" cy="116" r="0.9"',
            '        fill="#ffffff" opacity="0.9" />',
            '    <circle cx="92" cy="96" r="0.8"',
            '        fill="#ffffff" opacity="0.9" />',
            '</g>',
        ]
        return "\n".join(fancy_parts)
    else:
        # plain tree
        return '''<g>
    <!-- plain layered green foliage (no decorations) -->
    <polygon points="50,185 100,115 150,185" fill="#0b6623" />
    <polygon points="60,155 100,95 140,155" fill="#0b6623" />
    <polygon points="70,130 100,70 130,130" fill="#0b6623" />
</g>'''


def get_snowman_decoration() -> str:
    """Generate snowman decoration SVG."""
    return '''<g>
    <!-- bottom snowball -->
    <circle cx="100" cy="160" r="35" fill="#ffffff" stroke="#e0e0e0" stroke-width="1.5"/>
    <!-- middle snowball -->
    <circle cx="100" cy="110" r="28" fill="#ffffff" stroke="#e0e0e0" stroke-width="1.5"/>
    <!-- top snowball (head) -->
    <circle cx="100" cy="65" r="22" fill="#ffffff" stroke="#e0e0e0" stroke-width="1.5"/>
    <!-- hat brim -->
    <ellipse cx="100" cy="48" rx="28" ry="5" fill="#2c2c2c"/>
    <!-- hat top -->
    <rect x="80" y="25" width="40" height="23" fill="#2c2c2c" rx="2"/>
    <!-- hat band -->
    <rect x="80" y="40" width="40" height="4" fill="#b71c1c"/>
    <!-- eyes -->
    <circle cx="92" cy="62" r="2.5" fill="#2c2c2c"/>
    <circle cx="108" cy="62" r="2.5" fill="#2c2c2c"/>
    <!-- carrot nose -->
    <polygon points="100,68 105,70 100,72" fill="#ff6f00"/>
    <!-- smile (coal pieces) -->
    <circle cx="92" cy="75" r="1.5" fill="#2c2c2c"/>
    <circle cx="96" cy="77" r="1.5" fill="#2c2c2c"/>
    <circle cx="100" cy="78" r="1.5" fill="#2c2c2c"/>
    <circle cx="104" cy="77" r="1.5" fill="#2c2c2c"/>
    <circle cx="108" cy="75" r="1.5" fill="#2c2c2c"/>
    <!-- buttons -->
    <circle cx="100" cy="100" r="3" fill="#2c2c2c"/>
    <circle cx="100" cy="115" r="3" fill="#2c2c2c"/>
    <circle cx="100" cy="130" r="3" fill="#2c2c2c"/>
    <!-- scarf -->
    <path d="M78,80 Q100,85 122,80" fill="none" stroke="#b71c1c" stroke-width="6" stroke-linecap="round"/>
    <path d="M78,84 Q100,89 122,84" fill="none" stroke="#c62828" stroke-width="4" stroke-linecap="round"/>
    <!-- scarf tail -->
    <path d="M78,80 L70,95 L72,100" fill="#b71c1c" stroke="#8b0000" stroke-width="0.8"/>
</g>'''


def get_santa_decoration() -> str:
    """Generate Santa face decoration SVG."""
    return '''<g>
    <!-- face -->
    <circle cx="100" cy="100" r="45" fill="#fdd0b5"/>
    <!-- hat -->
    <!-- adjust hat so it sits naturally on the head (slightly nudged up by 1px) -->
    <path d="M60,72 Q100,37 140,72 L140,82 Q100,87 60,82 Z" fill="#b71c1c"/>
    <ellipse cx="100" cy="82" rx="42" ry="6" fill="#ffffff"/>
    <!-- hat pom-pom (nudged up to match brim) -->
    <circle cx="100" cy="49" r="8" fill="#ffffff"/>
    <!-- eyes -->
    <circle cx="85" cy="95" r="4" fill="#2c2c2c"/>
    <circle cx="115" cy="95" r="4" fill="#2c2c2c"/>
    <!-- rosy cheeks (moved slightly farther from the nose and kept aligned) -->
    <circle cx="70" cy="105" r="7" fill="#ff8a80" opacity="0.6"/>
    <circle cx="130" cy="105" r="7" fill="#ff8a80" opacity="0.6"/>
    <!-- nose -->
    <ellipse cx="100" cy="105" rx="5" ry="6" fill="#ff6b6b"/>
    <!-- mustache (brought the two pieces slightly closer together) -->
    <ellipse cx="87" cy="115" rx="12" ry="5" fill="#ffffff"/>
    <ellipse cx="113" cy="115" rx="12" ry="5" fill="#ffffff"/>
    <!-- beard -->
    <path d="M70,120 Q100,155 130,120 Q125,140 100,145 Q75,140 70,120" fill="#ffffff"/>
    <!-- beard details (curls) -->
    <circle cx="80" cy="130" r="5" fill="#f5f5f5"/>
    <circle cx="100" cy="138" r="5" fill="#f5f5f5"/>
    <circle cx="120" cy="130" r="5" fill="#f5f5f5"/>
    <!-- smile (moved slightly lower) -->
    <path d="M92,124 Q100,128 108,124" fill="none" stroke="#8b4513" stroke-width="1.5" stroke-linecap="round"/>
</g>'''


def get_gift_decoration() -> str:
    """Generate wrapped gift box decoration SVG."""
    return '''<g>
    <!-- gift box -->
    <rect x="60" y="100" width="80" height="70" fill="#b71c1c" stroke="#8b0000" stroke-width="1.5" rx="3"/>
    <!-- vertical ribbon -->
    <rect x="95" y="100" width="10" height="70" fill="#ffd54a"/>
    <!-- horizontal ribbon -->
    <rect x="60" y="130" width="80" height="10" fill="#ffd54a"/>
    <!-- bow loops -->
    <ellipse cx="85" cy="95" rx="12" ry="8" fill="#ffd54a" stroke="#daa520" stroke-width="1"/>
    <ellipse cx="115" cy="95" rx="12" ry="8" fill="#ffd54a" stroke="#daa520" stroke-width="1"/>
    <!-- bow center -->
    <circle cx="100" cy="95" r="6" fill="#ffb300"/>
    <!-- bow tails -->
    <path d="M85,103 L78,115 L80,118" fill="#ffd54a" stroke="#daa520" stroke-width="0.8"/>
    <path d="M115,103 L122,115 L120,118" fill="#ffd54a" stroke="#daa520" stroke-width="0.8"/>
    <!-- box highlights -->
    <rect x="62" y="102" width="3" height="20" fill="#ffffff" opacity="0.3"/>
    <!-- ribbon shine -->
    <rect x="96" y="102" width="2" height="15" fill="#ffffff" opacity="0.5"/>
</g>'''


def get_star_decoration() -> str:
    """Generate decorative star SVG."""
    return '''<g>
    <!-- large outer star -->
    <polygon points="100,50 110,85 145,90 120,112 128,147 100,130 72,147 80,112 55,90 90,85"
        fill="#ffd54a" stroke="#daa520" stroke-width="2"/>
    <!-- inner star for depth -->
    <polygon points="100,70 105,90 120,93 110,105 113,120 100,110 87,120 90,105 80,93 95,90"
        fill="#fff176"/>
    <!-- center highlight -->
    <circle cx="100" cy="100" r="8" fill="#ffeb3b"/>
</g>'''


def get_candy_cane_decoration() -> str:
    """Generate candy cane decoration SVG."""
    return '''<g transform="translate(230,12) scale(-1,1)">
    <!-- main cane shape -->
    <path d="M100,180 L100,100 Q100,70 120,70 Q140,70 140,90 Q140,110 120,110"
        fill="none" stroke="#ffffff" stroke-width="16" stroke-linecap="round"/>
    <!-- red stripes (spaced out to avoid overlap) -->
    <path d="M100,175 L100,162" stroke="#b71c1c" stroke-width="16" stroke-linecap="round"/>
    <path d="M100,150 L100,136" stroke="#b71c1c" stroke-width="16" stroke-linecap="round"/>
    <path d="M100,125 L100,110" stroke="#b71c1c" stroke-width="16" stroke-linecap="round"/>
    <path d="M102,96 Q102,70 120,70" stroke="#b71c1c" stroke-width="16" stroke-linecap="round"/>
    <path d="M122,72 Q132,72 132,84" stroke="#b71c1c" stroke-width="16" stroke-linecap="round"/>
    <path d="M132,96 Q132,103 124,105" stroke="#b71c1c" stroke-width="16" stroke-linecap="round"/>
    <!-- highlight/shine -->
    <path d="M95,170 L95,105" stroke="#ffffff" stroke-width="3" opacity="0.6" stroke-linecap="round"/>
</g>'''


def get_bell_decoration() -> str:
    """Generate Christmas bell decoration SVG."""
    return '''<g>
    <!-- bell body (reduced size) -->
    <path d="M72,100 Q72,82 100,82 Q128,82 128,100 L132,126 Q132,134 122,140 L122,144 Q122,148 100,148 Q78,148 78,144 L78,140 Q68,134 68,126 Z"
        fill="#ffd54a" stroke="#d3a21a" stroke-width="1.5"/>
    <!-- bell rim (slightly raised) -->
    <ellipse cx="100" cy="148" rx="26" ry="7" fill="#d3a21a"/>
    <!-- bell clapper (slightly higher) -->
    <ellipse cx="100" cy="156" rx="5" ry="6" fill="#8b0000"/>
    <!-- ribbon/bow on top (moved down to sit on bell) -->
    <path d="M90,80 Q100,76 110,80" fill="none" stroke="#b71c1c" stroke-width="3.5" stroke-linecap="round"/>
    <circle cx="88" cy="78" r="4.5" fill="#b71c1c"/>
    <circle cx="112" cy="78" r="4.5" fill="#b71c1c"/>
    <!-- bell highlights (more visible) -->
    <ellipse cx="86" cy="94" rx="10" ry="16" fill="#ffffff" opacity="0.45"/>
    <path d="M76,108 Q80,126 84,136" fill="none" stroke="#ffffff" stroke-width="2.5" opacity="0.35"/>
    <!-- decorative holly -->
    <circle cx="95" cy="82" r="3" fill="#b71c1c"/>
    <circle cx="105" cy="82" r="3" fill="#b71c1c"/>
    <ellipse cx="92" cy="79" rx="4" ry="3" fill="#2e7d32"/>
    <ellipse cx="100" cy="78" rx="4" ry="3" fill="#2e7d32"/>
    <ellipse cx="108" cy="79" rx="4" ry="3" fill="#2e7d32"/>
</g>'''


def generate_svg(
    url: str,
    foreground_color: str = '#0b6623',
    background_color: str = '#ffffff',
    decorate: bool = True,
    border: int = 8,
    reserve_mode: str = 'overlay',
    logo_pos: str = 'bottom-right',
    logo_size_pct: float = 20.0,
    ecc: str = 'H',
    tree_style: str = 'fancy',
    decoration_type: str = 'tree',
) -> str:
    """Generate an embeddable SVG string for the given URL.

    The returned SVG is safe to inline into HTML (no prolog/doctype). It will
    have width/height set to 250 and a viewBox inserted if missing.
    """
    # Create QR with requested error correction level.
    # Use no background fill (light=None) to create a transparent QR code that allows CSS-based coloring
    qr = segno.make(url, micro=False, error=ecc)
    svg = qr.svg_inline(
        dark=foreground_color, light=None, border=border
    )

    # Replace stroke colors with currentColor so CSS can control QR color.
    # QR codes rendered by segno use stroke (not fill) for the modules.
    # Match hex colors (e.g., #0b6623, #000, #000000)
    svg = re.sub(
        r'stroke=["\']#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})["\']',
        'stroke="currentColor"',
        svg
    )

    # Also replace RGB stroke colors if present
    svg = re.sub(
        r'stroke=["\']rgb\([^)]+\)["\']',
        'stroke="currentColor"',
        svg
    )

    # Replace stroke declarations inside style attributes
    def _fix_style(m):
        s = m.group(1)
        s = re.sub(
            r'(?i)stroke\s*:\s*#[0-9a-fA-F]{3,6}',
            'stroke:currentColor',
            s,
        )
        s = re.sub(
            r'(?i)stroke\s*:\s*rgb\([^)]+\)',
            'stroke:currentColor',
            s,
        )
        return f'style="{s}"'

    svg = re.sub(r'(?i)style\s*=\s*"([^"]*)"', _fix_style, svg)

    # Ensure the root <svg> has helpful classes and a data attribute with the
    # default foreground color. Add both 'qr-svg' and 'qrcode-box' classes
    # to support CSS-based coloring.
    def _add_data_attr(m):
        tag = m.group(1)
        attrs = m.group(2) or ''
        # Ensure the existing segno class is preserved and that both
        # "qr-svg" and "qrcode-box" classes are present. The
        # "qr-svg" class is required for correct color handling when
        # the SVG uses `currentColor` with transparency.
        if re.search(r'\bclass\s*=\s*"', attrs) is None:
            # No existing class attribute: add both qr-svg and qrcode-box
            attrs += ' class="qr-svg qrcode-box"'
        else:
            # Existing class attribute: ensure both qr-svg and qrcode-box are present
            class_match = re.search(r'class="([^"]*)"', attrs)
            if class_match:
                existing_classes = class_match.group(1).split()
                if 'qr-svg' not in existing_classes:
                    existing_classes.append('qr-svg')
                if 'qrcode-box' not in existing_classes:
                    existing_classes.append('qrcode-box')
                new_class_value = ' '.join(existing_classes)
                attrs = (
                    attrs[:class_match.start(1)]
                    + new_class_value
                    + attrs[class_match.end(1):]
                )
        # expose the default foreground color so CSS can override via
        # currentColor
        data_attr_pat = r'\bdata-qr-default-foreground-color\s*=\s*"'
        if re.search(data_attr_pat, attrs) is None:
            attrs += f' data-qr-default-foreground-color="{foreground_color}"'
        return f'{tag}{attrs}'

    svg = re.sub(r'(<svg\b)([^>]*)', _add_data_attr, svg, count=1)

    # Determine internal SVG coordinate system (viewBox or width/height)
    vb_w = vb_h = None
    m = re.search(
        r'viewBox="0 0 (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)"', svg
    )
    if m:
        vb_w = float(m.group(1))
        vb_h = float(m.group(2))
    else:
        m2 = re.search(
            r'width="(\d+(?:\.\d+)?)"\s+'
            r'height="(\d+(?:\.\d+)?)"',
            svg,
        )
        if m2:
            vb_w = float(m2.group(1))
            vb_h = float(m2.group(2))

    if vb_w is None or vb_h is None:
        vb_w = vb_h = 250.0

    # Default decorative size (reference coordinates are 200x200)
    deco_width = vb_w * 0.46
    deco_height = vb_h * 0.46

    # Default quietzone placement: centered along bottom with a small margin
    margin = vb_h * 0.02
    q_tx = (vb_w - deco_width) / 2.0
    q_ty = vb_h - deco_height - margin

    # Get the appropriate decoration based on type
    decoration_map = {
        'tree': lambda: get_tree_decoration(tree_style),
        'snowman': get_snowman_decoration,
        'santa': get_santa_decoration,
        'gift': get_gift_decoration,
        'star': get_star_decoration,
        'candy-cane': get_candy_cane_decoration,
        'bell': get_bell_decoration,
    }

    # Get decoration content
    if decoration_type in decoration_map:
        if decoration_type == 'tree':
            chosen_inner = decoration_map[decoration_type]()
        else:
            chosen_inner = decoration_map[decoration_type]()
    else:
        # Default to fancy tree if unknown type
        chosen_inner = get_tree_decoration('fancy')

    quiet_deco_group = (
        f'<g id="xmas-decoration" '
        f'transform="translate({q_tx:.2f}, {q_ty:.2f}) '
        f'scale({deco_width / 200.0:.6f})" aria-hidden="true">\n'
        f'{chosen_inner}\n'
        '</g>\n'
    )

    # If reserve_mode is overlay, compute placement based on reserved rect and
    # allow an overlay multiplier and shift
    deco_group = quiet_deco_group
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

        ov_raw = globals().get('__overlay_multiplier__', 1.15)
        overlay_multiplier = float(ov_raw)
        desired_w = rect_w * overlay_multiplier
        desired_h = rect_h * overlay_multiplier
        scale = desired_w / 200.0

        # Anchor tree so its bottom-right lines up with rect's bottom-right for
        # bottom-right position
        tx = rect_x + rect_w - desired_w
        ty = rect_y + rect_h - desired_h

        # apply horizontal shift (positive moves right)
        overlay_shift_x = float(globals().get('__overlay_shift_x__', 0.0))
        tx = tx + (rect_w * overlay_shift_x)
        # apply vertical shift (positive moves down)
        overlay_shift_y = float(globals().get('__overlay_shift_y__', 0.0))
        ty = ty + (rect_h * overlay_shift_y)

        # Decoration-specific nudges to tweak visual placement per decoration
        # These are small, conservative offsets expressed relative to the
        # reserved rect size so they scale with SVG size.
        if decoration_type == 'bell':
            # bell should be slightly lower and right
            tx += rect_w * 0.10
            ty += rect_h * 0.12
        elif decoration_type == 'star':
            # star tends to sit too high; nudge downward (much bigger nudge)
            tx += rect_w * 0.10
            ty += rect_h * 0.50
        elif decoration_type == 'santa':
            # santa was sitting too high (match star nudge)
            ty += rect_h * 0.50
        elif decoration_type == 'snowman':
            # snowman should be shifted slightly to the right
            tx += rect_w * 0.06
            ty += rect_h * 0.45
        elif decoration_type == 'gift':
            # gift should move slightly right
            tx += rect_w * 0.05

        # Build overlay variant using the chosen inner content
        deco_group = (
            f'<g id="xmas-decoration" '
            f'transform="translate({tx:.2f}, {ty:.2f}) '
            f'scale({scale:.6f})" aria-hidden="true">\n'
            f'{chosen_inner}\n'
            '</g>\n'
        )

    # Insert the deco_group before the closing </svg> only when decoration is
    # enabled
    if decorate and svg.strip().endswith('</svg>'):
        svg = svg.rstrip()[:-6] + '\n' + deco_group + '</svg>'

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


def sanitize_svg_for_html(svg: str, pretty: bool = True, indent_spaces: int = 2) -> str:
    """Strip XML prolog and DOCTYPE so the SVG is safe to embed directly
    in HTML."""
    # remove XML prolog like <?xml version="1.0" encoding="utf-8"?>
    svg = re.sub(r'^\s*<\?xml[^>]*>\s*', '', svg)
    # remove DOCTYPE declarations
    svg = re.sub(r'<!DOCTYPE[^>]*>\s*', '', svg, flags=re.I)

    # If pretty is disabled, return the cleaned SVG unchanged.
    if not pretty:
        # Minify by collapsing inter-tag whitespace so the SVG is compact
        compact = re.sub(r'>\s+<', '><', svg)
        return compact.strip() + '\n'

    # Try to pretty-format the SVG so it's easier for humans to read/edit.
    # Use xml.dom.minidom which indents elements; if parsing fails, fall
    # back to returning the cleaned SVG unchanged.
    try:
        from xml.dom import minidom

        # minidom expects a bytes/string containing XML; parse and
        # then produce an indented representation. toprettyxml may add
        # an XML prolog, so strip it afterwards.
        doc = minidom.parseString(svg)
        indent_str = ' ' * int(indent_spaces)
        pretty = doc.toprettyxml(indent=indent_str)
        # strip any leading XML prolog that toprettyxml may have added
        pretty = re.sub(r'^\s*<\?xml[^>]*>\s*', '', pretty)
        # remove any DOCTYPE that might have been introduced
        pretty = re.sub(r'<!DOCTYPE[^>]*>\s*', '', pretty, flags=re.I)

        # minidom inserts extra blank lines between text nodes; normalize
        # sequences of more than one blank line to a single newline.
        pretty = re.sub(r'\n{2,}', '\n', pretty)
        return pretty.strip() + '\n'
    except Exception:
        return svg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--root-domain',
        dest='root_domain',
        default=os.environ.get('ROOT_DOMAIN', 'https://example.com'),
        help='Root domain to build public URLs (can also be set via ROOT_DOMAIN env var)',
    )
    parser.add_argument('--pattern', default='*.html')
    parser.add_argument('--out-dir', default='scripts/generated_qr')
    parser.add_argument(
        '--minify',
        dest='minify',
        action='store_true',
        default=False,
        help='Write compact SVG without pretty-printing (faster, less readable)',
    )
    parser.add_argument(
        '--indent',
        dest='indent',
        type=int,
        choices=[2, 4],
        default=2,
        help='Number of spaces to use when pretty-printing SVG (2 or 4).',
    )
    parser.add_argument(
        '--foreground-color',
        dest='foreground_color',
        default='#0b6623',
        help='Foreground color for QR modules',
    )
    parser.add_argument(
        '--background-color',
        dest='background_color',
        default='#ffffff',
        help='Background color for QR',
    )
    parser.add_argument(
        '--no-decorate',
        dest='decorate',
        action='store_false',
        default=True,
        help='Disable decorative tree (opt-out)',
    )
    # Decoration is opt-out via --no-decorate; when decorating we reserve a
    # bottom-right overlay by default.
    parser.add_argument(
        '--logo-size',
        type=float,
        default=20.0,
        help='Percentage size for reserved logo area (percent of SVG width)',
    )
    parser.add_argument(
        '--overlay-mult',
        type=float,
        default=3.0,
        help='Multiplier to make overlayed tree slightly larger than reserved rect',
    )
    parser.add_argument(
        '--overlay-shift-x',
        type=float,
        default=0.90,
        help=(
            'Horizontal shift for overlay tree as fraction of reserved '
            'rect width (positive shifts right)'
        ),
    )
    parser.add_argument(
        '--overlay-shift-y',
        type=float,
        default=0.50,
        help=(
            'Vertical shift for overlay tree as fraction of reserved '
            'rect height (positive shifts down)'
        ),
    )
    parser.add_argument(
        '--ecc',
        choices=['L', 'M', 'Q', 'H'],
        default='H',
        help=(
            'Error correction level to use when generating QR '
            '(higher required for reserve modes)'
        ),
    )
    parser.add_argument(
        '--tree-style',
        choices=['fancy', 'plain'],
        default='fancy',
        help=(
            'Style of tree to render: fancy (default) or plain '
            '(no decorations)'
        ),
    )
    parser.add_argument(
        '--decoration-type',
        choices=['tree', 'snowman', 'santa', 'gift', 'star', 'candy-cane', 'bell'],
        default='tree',
        help=(
            'Type of decoration to overlay: tree (default), snowman, santa, '
            'gift, star, candy-cane, or bell. Only tree supports style variants.'
        ),
    )
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    files = glob.glob(args.pattern)
    if not files:
        print('No files found matching pattern')
        return 0

    for path in files:
        basename = os.path.splitext(os.path.basename(path))[0]
        public_url = urllib.parse.urljoin(
            args.root_domain.rstrip('/') + '/',
            urllib.parse.quote(os.path.basename(path)),
        )

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
        # Per-page override for decoration type
        decoration_type = args.decoration_type
        if 'qr-decoration-type' in meta:
            v = meta.get('qr-decoration-type', '').strip().lower()
            if v in ('tree', 'snowman', 'santa', 'gift', 'star', 'candy-cane', 'bell'):
                decoration_type = v
            else:
                # ignore invalid values and leave as CLI/default
                pass

        # Decide reserve behavior: this project places the decorative
        # overlay in the bottom-right by default when decoration is
        # enabled. Decoration is opt-out via --no-decorate.
        if decorate:
            reserve_mode = 'overlay'
            logo_pos = 'bottom-right'
        else:
            reserve_mode = None
            logo_pos = 'center'

        # If using overlay, render QR with no border so it fills the viewBox entirely
        border = 0 if reserve_mode == 'overlay' else 8
        # Expose overlay multiplier & horizontal/vertical shift globally
        # for the generator (quick way to pass through)
        globals()['__overlay_multiplier__'] = args.overlay_mult
        globals()['__overlay_shift_x__'] = args.overlay_shift_x
        globals()['__overlay_shift_y__'] = args.overlay_shift_y

        svg = generate_svg(
            public_url,
            foreground_color=foreground,
            background_color=background,
            decorate=decorate,
            border=border,
            reserve_mode=reserve_mode,
            logo_pos=logo_pos,
            logo_size_pct=args.logo_size,
            ecc=args.ecc,
            tree_style=tree_style,
            decoration_type=decoration_type,
        )

        out_path = os.path.join(args.out_dir, f'{basename}.svg')
        # Pretty-print with requested indent unless minify requested
        svg = sanitize_svg_for_html(svg, pretty=not args.minify, indent_spaces=args.indent)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(svg)
        print(f'Generated {out_path} for {public_url}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
