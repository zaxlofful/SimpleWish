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
    """Generate Christmas tree decoration SVG (fancy or plain) - remade from scratch."""
    if style == 'fancy':
        # Completely new fancy tree design with three tiers and decorations
        # Using the expected green color #0b6623
        fancy_parts = [
            '<g>',
            '    <!-- bottom tier of tree -->',
            '    <polygon points="45,180 100,120 155,180"',
            '        fill="#0b6623" stroke="#094d1a" stroke-width="0.5"/>',
            '    <!-- middle tier -->',
            '    <polygon points="55,145 100,90 145,145"',
            '        fill="#0b6623" stroke="#094d1a" stroke-width="0.5"/>',
            '    <!-- top tier -->',
            '    <polygon points="65,115 100,60 135,115"',
            '        fill="#0b6623" stroke="#094d1a" stroke-width="0.5"/>',
            '    <!-- star topper -->',
            '    <polygon points="100,50 103,59 112,60 105,66 107,75 100,70 93,75 95,66 88,60 97,59"',
            '        fill="#ffeb3b" stroke="#f9a825" stroke-width="0.8"/>',
            '    <!-- trunk -->',
            '    <rect x="95" y="180" width="10" height="15"',
            '        fill="#5d4037" stroke="#3e2723" stroke-width="0.5"/>',
            '    <!-- red ornaments (using #b71c1c) -->',
            '    <circle cx="85" cy="135" r="3.5" fill="#b71c1c" stroke="#8b0000" stroke-width="0.5"/>',
            '    <circle cx="115" cy="140" r="3" fill="#e53935" stroke="#b71c1c" stroke-width="0.5"/>',
            '    <circle cx="100" cy="155" r="3.2" fill="#f44336" stroke="#d32f2f" stroke-width="0.5"/>',
            '    <!-- gold ornaments (using #ffd54a) -->',
            '    <circle cx="75" cy="150" r="2.8" fill="#ffd54a" stroke="#fbc02d" stroke-width="0.5"/>',
            '    <circle cx="125" cy="155" r="2.5" fill="#ffeb3b" stroke="#fdd835" stroke-width="0.5"/>',
            '    <!-- blue ornaments -->',
            '    <circle cx="95" cy="125" r="2.6" fill="#1976d2" stroke="#0d47a1" stroke-width="0.5"/>',
            '    <circle cx="110" cy="115" r="2.4" fill="#2196f3" stroke="#1565c0" stroke-width="0.5"/>',
            '    <!-- string lights -->',
            '    <circle cx="70" cy="138" r="1.5" fill="#fff59d" opacity="0.9"/>',
            '    <circle cx="90" cy="145" r="1.5" fill="#ffccbc" opacity="0.9"/>',
            '    <circle cx="110" cy="148" r="1.5" fill="#b3e5fc" opacity="0.9"/>',
            '    <circle cx="130" cy="142" r="1.5" fill="#c5e1a5" opacity="0.9"/>',
            '    <!-- garland swag -->',
            '    <path d="M70,130 Q100,140 130,130" fill="none" stroke="#8bc34a" stroke-width="2" opacity="0.8"/>',
            '    <path d="M60,150 Q100,162 140,150" fill="none" stroke="#7cb342" stroke-width="2.5" opacity="0.8"/>',
            '</g>',
        ]
        return "\n".join(fancy_parts)
    else:
        # Simple plain tree - minimalist design with #0b6623 green
        return '''<g>
    <!-- simple three-tier tree -->
    <polygon points="50,175 100,125 150,175" fill="#0b6623"/>
    <polygon points="60,145 100,95 140,145" fill="#0b6623"/>
    <polygon points="70,120 100,70 130,120" fill="#0b6623"/>
    <!-- simple trunk -->
    <rect x="93" y="175" width="14" height="18" fill="#6d4c41"/>
</g>'''


def get_snowman_decoration() -> str:
    """Generate snowman decoration SVG - remade from scratch."""
    return '''<g>
    <!-- base snowball (largest) -->
    <circle cx="100" cy="165" r="32" fill="#fafafa" stroke="#cfd8dc" stroke-width="1.2"/>
    <!-- middle snowball -->
    <circle cx="100" cy="115" r="26" fill="#ffffff" stroke="#cfd8dc" stroke-width="1.2"/>
    <!-- head snowball (smallest) -->
    <circle cx="100" cy="72" r="20" fill="#ffffff" stroke="#cfd8dc" stroke-width="1.2"/>
    <!-- top hat brim -->
    <ellipse cx="100" cy="56" rx="26" ry="4.5" fill="#212121"/>
    <!-- top hat cylinder -->
    <rect x="82" y="35" width="36" height="21" fill="#424242" rx="1.5"/>
    <!-- hat band with holly -->
    <rect x="82" y="48" width="36" height="5" fill="#c62828"/>
    <circle cx="96" cy="50" r="1.8" fill="#c62828"/>
    <circle cx="104" cy="50" r="1.8" fill="#c62828"/>
    <!-- coal eyes -->
    <circle cx="92" cy="68" r="2.2" fill="#212121"/>
    <circle cx="108" cy="68" r="2.2" fill="#212121"/>
    <!-- carrot nose - more prominent -->
    <path d="M100,74 L108,76 L100,78 Z" fill="#ff6f00" stroke="#e65100" stroke-width="0.4"/>
    <!-- coal smile -->
    <circle cx="90" cy="82" r="1.3" fill="#212121"/>
    <circle cx="94" cy="84" r="1.3" fill="#212121"/>
    <circle cx="100" cy="85" r="1.3" fill="#212121"/>
    <circle cx="106" cy="84" r="1.3" fill="#212121"/>
    <circle cx="110" cy="82" r="1.3" fill="#212121"/>
    <!-- coal buttons on body -->
    <circle cx="100" cy="105" r="2.8" fill="#212121"/>
    <circle cx="100" cy="120" r="2.8" fill="#212121"/>
    <circle cx="100" cy="135" r="2.8" fill="#212121"/>
    <circle cx="100" cy="150" r="2.8" fill="#212121"/>
    <!-- knitted scarf -->
    <path d="M75,88 Q100,93 125,88" fill="none" stroke="#1565c0" stroke-width="7" stroke-linecap="round"/>
    <path d="M75,92 Q100,97 125,92" fill="none" stroke="#1976d2" stroke-width="5" stroke-linecap="round"/>
    <!-- scarf ends -->
    <rect x="72" y="88" width="7" height="20" fill="#1565c0" rx="1"/>
    <rect x="121" y="88" width="7" height="20" fill="#1976d2" rx="1"/>
    <!-- scarf fringe -->
    <line x1="73" y1="108" x2="73" y2="112" stroke="#0d47a1" stroke-width="1.5"/>
    <line x1="77" y1="108" x2="77" y2="114" stroke="#0d47a1" stroke-width="1.5"/>
    <line x1="123" y1="108" x2="123" y2="113" stroke="#0d47a1" stroke-width="1.5"/>
    <line x1="127" y1="108" x2="127" y2="111" stroke="#0d47a1" stroke-width="1.5"/>
</g>'''


def get_santa_decoration() -> str:
    """Generate Santa face decoration SVG - remade from scratch."""
    return '''<g>
    <!-- face circle -->
    <circle cx="100" cy="105" r="42" fill="#ffccbc"/>
    <!-- santa hat (using #b71c1c red) -->
    <path d="M62,82 Q100,45 138,82 L138,90 L62,90 Z" fill="#b71c1c"/>
    <!-- hat trim -->
    <ellipse cx="100" cy="90" rx="38" ry="5.5" fill="#f5f5f5"/>
    <!-- pom-pom -->
    <circle cx="100" cy="52" r="7.5" fill="#f5f5f5" stroke="#eeeeee" stroke-width="0.6"/>
    <!-- eyes with sparkle -->
    <circle cx="86" cy="100" r="4.5" fill="#424242"/>
    <circle cx="88" cy="98" r="1.5" fill="#ffffff"/>
    <circle cx="114" cy="100" r="4.5" fill="#424242"/>
    <circle cx="116" cy="98" r="1.5" fill="#ffffff"/>
    <!-- rosy cheeks -->
    <ellipse cx="68" cy="110" rx="8" ry="6" fill="#ef9a9a" opacity="0.7"/>
    <ellipse cx="132" cy="110" rx="8" ry="6" fill="#ef9a9a" opacity="0.7"/>
    <!-- nose -->
    <ellipse cx="100" cy="108" rx="6" ry="7" fill="#ff8a80"/>
    <ellipse cx="98" cy="106" rx="2" ry="2.5" fill="#ffcdd2" opacity="0.6"/>
    <!-- bushy mustache -->
    <ellipse cx="82" cy="118" rx="14" ry="7" fill="#fafafa"/>
    <ellipse cx="118" cy="118" rx="14" ry="7" fill="#fafafa"/>
    <!-- mustache details -->
    <path d="M75,118 Q78,121 82,119" fill="none" stroke="#e0e0e0" stroke-width="1"/>
    <path d="M125,118 Q122,121 118,119" fill="none" stroke="#e0e0e0" stroke-width="1"/>
    <!-- fluffy beard -->
    <path d="M70,125 Q65,140 70,150 Q85,155 100,152 Q115,155 130,150 Q135,140 130,125 Q115,130 100,128 Q85,130 70,125" fill="#fafafa"/>
    <!-- beard texture -->
    <circle cx="80" cy="135" r="4.5" fill="#f5f5f5" opacity="0.8"/>
    <circle cx="100" cy="140" r="5" fill="#f5f5f5" opacity="0.8"/>
    <circle cx="120" cy="135" r="4.5" fill="#f5f5f5" opacity="0.8"/>
    <circle cx="90" cy="145" r="3.5" fill="#f5f5f5" opacity="0.8"/>
    <circle cx="110" cy="145" r="3.5" fill="#f5f5f5" opacity="0.8"/>
</g>'''


def get_gift_decoration() -> str:
    """Generate wrapped gift box decoration SVG - remade from scratch."""
    return '''<g>
    <!-- main gift box -->
    <rect x="65" y="110" width="70" height="60" fill="#c62828" stroke="#b71c1c" stroke-width="1.2" rx="2.5"/>
    <!-- box lid with shadow -->
    <rect x="62" y="100" width="76" height="12" fill="#d32f2f" stroke="#c62828" stroke-width="1" rx="2"/>
    <!-- vertical ribbon -->
    <rect x="95" y="100" width="10" height="70" fill="#ffd54a"/>
    <rect x="96.5" y="100" width="7" height="70" fill="#ffeb3b"/>
    <!-- horizontal ribbon -->
    <rect x="62" y="135" width="76" height="10" fill="#ffd54a"/>
    <rect x="62" y="136.5" width="76" height="7" fill="#ffeb3b"/>
    <!-- ribbon shine effect -->
    <rect x="97" y="102" width="2" height="20" fill="#ffffff" opacity="0.4"/>
    <rect x="97" y="150" width="2" height="18" fill="#ffffff" opacity="0.4"/>
    <!-- bow - left loop -->
    <ellipse cx="88" cy="96" rx="10" ry="7" fill="#ffd54a" stroke="#f9a825" stroke-width="0.8"/>
    <ellipse cx="88" cy="96" rx="8" ry="5.5" fill="#ffeb3b"/>
    <!-- bow - right loop -->
    <ellipse cx="112" cy="96" rx="10" ry="7" fill="#ffd54a" stroke="#f9a825" stroke-width="0.8"/>
    <ellipse cx="112" cy="96" rx="8" ry="5.5" fill="#ffeb3b"/>
    <!-- bow center knot -->
    <circle cx="100" cy="96" r="5.5" fill="#f9a825" stroke="#f57f17" stroke-width="0.6"/>
    <!-- bow ribbons hanging -->
    <path d="M95,101 L90,112 L92,115" fill="#ffd54a" stroke="#f9a825" stroke-width="0.6"/>
    <path d="M105,101 L110,112 L108,115" fill="#ffeb3b" stroke="#f9a825" stroke-width="0.6"/>
    <!-- decorative corner highlights on box -->
    <circle cx="70" cy="115" r="2" fill="#ffeb3b" opacity="0.6"/>
    <circle cx="130" cy="115" r="2" fill="#ffeb3b" opacity="0.6"/>
    <circle cx="70" cy="165" r="2" fill="#ffeb3b" opacity="0.6"/>
    <circle cx="130" cy="165" r="2" fill="#ffeb3b" opacity="0.6"/>
</g>'''


def get_star_decoration() -> str:
    """Generate decorative star SVG - remade from scratch."""
    return '''<g>
    <!-- outer star with gradient-like layering -->
    <polygon points="100,55 112,88 147,93 123,115 130,150 100,133 70,150 77,115 53,93 88,88"
        fill="#fdd835" stroke="#f9a825" stroke-width="1.8"/>
    <!-- middle star layer -->
    <polygon points="100,68 108,92 132,96 116,111 120,135 100,122 80,135 84,111 68,96 92,92"
        fill="#ffeb3b" stroke="#fbc02d" stroke-width="1.2"/>
    <!-- inner star for depth -->
    <polygon points="100,78 105,95 122,98 113,107 116,124 100,115 84,124 87,107 78,98 95,95"
        fill="#fff9c4"/>
    <!-- center brilliant point -->
    <circle cx="100" cy="100" r="9" fill="#fffde7"/>
    <circle cx="100" cy="100" r="5" fill="#ffffff" opacity="0.9"/>
    <!-- radiating sparkles -->
    <circle cx="100" cy="62" r="2.5" fill="#ffffff" opacity="0.85"/>
    <circle cx="138" cy="93" r="2.2" fill="#ffffff" opacity="0.85"/>
    <circle cx="126" cy="140" r="2.2" fill="#ffffff" opacity="0.85"/>
    <circle cx="74" cy="140" r="2.2" fill="#ffffff" opacity="0.85"/>
    <circle cx="62" cy="93" r="2.2" fill="#ffffff" opacity="0.85"/>
</g>'''


def get_candy_cane_decoration() -> str:
    """Generate candy cane decoration SVG - remade from scratch."""
    return '''<g>
    <!-- candy cane main body - white base -->
    <path d="M100,180 L100,105 Q100,75 120,75 Q140,75 140,95 Q140,115 120,115"
        fill="none" stroke="#fafafa" stroke-width="18" stroke-linecap="round"/>
    <!-- red candy stripes (diagonal pattern) -->
    <path d="M100,172 L100,158" stroke="#d32f2f" stroke-width="18" stroke-linecap="round"/>
    <path d="M100,146 L100,132" stroke="#d32f2f" stroke-width="18" stroke-linecap="round"/>
    <path d="M100,120 L100,106" stroke="#d32f2f" stroke-width="18" stroke-linecap="round"/>
    <!-- curved top stripes -->
    <path d="M102,98 Q102,75 120,75" stroke="#d32f2f" stroke-width="18" stroke-linecap="round"/>
    <path d="M122,77 Q132,77 132,87" stroke="#d32f2f" stroke-width="18" stroke-linecap="round"/>
    <path d="M132,99 Q132,108 124,112" stroke="#d32f2f" stroke-width="18" stroke-linecap="round"/>
    <!-- highlight shine on left edge -->
    <path d="M94,175 L94,108" stroke="#ffffff" stroke-width="4" opacity="0.5" stroke-linecap="round"/>
    <path d="M96,100 Q96,78 116,78" stroke="#ffffff" stroke-width="3" opacity="0.5" stroke-linecap="round"/>
    <!-- shadow/depth on right edge -->
    <path d="M106,165 L106,115" stroke="#ef5350" stroke-width="2.5" opacity="0.4" stroke-linecap="round"/>
    <!-- decorative bow at top curve -->
    <ellipse cx="130" cy="95" rx="8" ry="6" fill="#c62828"/>
    <ellipse cx="145" cy="90" rx="7" ry="5" fill="#d32f2f"/>
    <circle cx="138" cy="92" r="4" fill="#b71c1c"/>
</g>'''


def get_bell_decoration() -> str:
    """Generate Christmas bell decoration SVG - remade from scratch."""
    return '''<g>
    <!-- bell body with traditional shape -->
    <path d="M75,105 Q75,88 100,88 Q125,88 125,105 L128,128 Q128,138 116,144 L116,148 Q116,152 100,152 Q84,152 84,148 L84,144 Q72,138 72,128 Z"
        fill="#ffb300" stroke="#f57f17" stroke-width="1.4"/>
    <!-- bell rim flare -->
    <ellipse cx="100" cy="152" rx="24" ry="6.5" fill="#f57f17"/>
    <ellipse cx="100" cy="151" rx="22" ry="5" fill="#ffc107"/>
    <!-- clapper inside bell -->
    <line x1="100" y1="148" x2="100" y2="158" stroke="#5d4037" stroke-width="2"/>
    <ellipse cx="100" cy="160" rx="4.5" ry="5.5" fill="#6d4c41"/>
    <ellipse cx="99" cy="159" rx="2" ry="2.5" fill="#8d6e63" opacity="0.6"/>
    <!-- decorative ribbon on top -->
    <path d="M88,86 Q100,82 112,86" fill="none" stroke="#c62828" stroke-width="4.5" stroke-linecap="round"/>
    <!-- ribbon bow loops -->
    <circle cx="86" cy="84" r="5" fill="#d32f2f"/>
    <circle cx="114" cy="84" r="5" fill="#d32f2f"/>
    <circle cx="100" cy="83" r="3.5" fill="#b71c1c"/>
    <!-- holly leaves on ribbon -->
    <ellipse cx="90" cy="82" rx="4.5" ry="3" fill="#43a047" transform="rotate(-20 90 82)"/>
    <ellipse cx="98" cy="80" rx="4.5" ry="3" fill="#4caf50"/>
    <ellipse cx="102" cy="80" rx="4.5" ry="3" fill="#4caf50"/>
    <ellipse cx="110" cy="82" rx="4.5" ry="3" fill="#43a047" transform="rotate(20 110 82)"/>
    <!-- holly berries -->
    <circle cx="94" cy="84" r="2.2" fill="#e53935"/>
    <circle cx="106" cy="84" r="2.2" fill="#e53935"/>
    <!-- bell highlights for metallic look -->
    <ellipse cx="88" cy="98" rx="9" ry="18" fill="#ffffff" opacity="0.35"/>
    <ellipse cx="85" cy="115" rx="6" ry="12" fill="#ffffff" opacity="0.25"/>
    <path d="M78,110 Q82,128 86,138" fill="none" stroke="#ffffff" stroke-width="2.5" opacity="0.2"/>
    <!-- decorative engravings on bell -->
    <path d="M90,135 Q100,138 110,135" fill="none" stroke="#f57f17" stroke-width="1.2" opacity="0.6"/>
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
    qr = segno.make(url, micro=False, error=ecc)
    svg = qr.svg_inline(
        dark=foreground_color, light=background_color, border=border
    )

    # Replace black fills with currentColor so CSS can recolor the QR
    rgb_pattern = r'(?i)fill=["\']\s*rgb\(\s*0\s*,\s*0\s*,\s*0\s*\)\s*["\']'
    hex0_pattern = r'(?i)fill=["\']\s*#0{3,6}\s*["\']'
    svg = re.sub(rgb_pattern, 'fill="currentColor"', svg)
    svg = re.sub(hex0_pattern, 'fill="currentColor"', svg)

    # Replace fill declarations inside style attributes
    def _fix_style(m):
        s = m.group(1)
        s = re.sub(
            r'(?i)fill\s*:\s*rgb\(\s*0\s*,\s*0\s*,\s*0\s*\)',
            'fill:currentColor',
            s,
        )
        s = re.sub(r'(?i)fill\s*:\s*#0{3,6}', 'fill:currentColor', s)
        return f'style="{s}"'

    svg = re.sub(r'(?i)style\s*=\s*"([^"]*)"', _fix_style, svg)

    # Ensure the root <svg> has a helpful class and a data attribute with the
    # default foreground color
    def _add_data_attr(m):
        tag = m.group(1)
        attrs = m.group(2) or ''
        if re.search(r'\bclass\s*=\s*"', attrs) is None:
            attrs += ' class="qr-svg"'
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


def sanitize_svg_for_html(svg: str) -> str:
    """Strip XML prolog and DOCTYPE so the SVG is safe to embed directly
    in HTML."""
    # remove XML prolog like <?xml version="1.0" encoding="utf-8"?>
    svg = re.sub(r'^\s*<\?xml[^>]*>\s*', '', svg)
    # remove DOCTYPE declarations
    svg = re.sub(r'<!DOCTYPE[^>]*>\s*', '', svg, flags=re.I)
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
        svg = sanitize_svg_for_html(svg)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(svg)
        print(f'Generated {out_path} for {public_url}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
