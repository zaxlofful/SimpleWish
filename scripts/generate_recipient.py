#!/usr/bin/env python3
"""Generate a per-recipient HTML file from the `index.html` template.

Usage:
    python scripts/generate_recipient.py --data recipients/elsa.json

The script reads `index.html`, applies values from the JSON data file,
and writes the resulting HTML to the output path (defaults to the
`filename` field in the data file or `<recipient>.html`).
"""
import argparse
import json
import re
import html
from pathlib import Path


def render_from_template(template_text: str, data: dict) -> str:
    s = template_text

    # Insert per-page meta tags for QR immediately after the QR metadata comment
    meta_block = []
    if data.get('qr_foreground'):
        meta_block.append(f'<meta name="qr-foreground-color" content="{html.escape(str(data["qr_foreground"]), quote=True)}">')
    if data.get('qr_background'):
        meta_block.append(f'<meta name="qr-background-color" content="{html.escape(str(data["qr_background"]), quote=True)}">')
    if data.get('qr_decor_type'):
        meta_block.append(f'<meta name="qr-decoration-type" content="{html.escape(str(data["qr_decor_type"]), quote=True)}">')
    meta_block_text = '\n  '.join(meta_block)

    # Try to insert after the QR metadata comment (the long comment block near head)
    s, n = re.subn(
        r'(<!-- QR metadata:.*?-->)',
        lambda m: m.group(1) + ('\n  ' + meta_block_text if meta_block_text else ''),
        s,
        flags=re.S,
    )

    # Update the <title> (escape for HTML)
    if 'title' in data:
        safe_title = html.escape(str(data['title']))
        s = re.sub(r'<title>.*?</title>', f'<title>{safe_title}</title>', s, flags=re.S)

    # Update recipient heading: <h1 id="recipient">...</h1>
    if 'recipient' in data:
        safe_recipient = html.escape(str(data['recipient']))
        new_h1 = f'Christmas List for {safe_recipient}'
        s = re.sub(r'(<h1\s+id="recipient">).*?(</h1>)', rf'\1{new_h1}\2', s, flags=re.S)

    # Update subtitle (.sub paragraph)
    if 'sub' in data:
        safe_sub = html.escape(str(data['sub']))
        s = re.sub(r'(<p class="sub">).*?(</p>)', rf'\1{safe_sub}\2', s, flags=re.S)

    # Update CSS variables --accent and --muted inside :root
    if 'accent' in data:
        # accent is a CSS color value; keep as provided but coerce to str
        s = re.sub(r'(--accent:\s*)[^;]+;', rf'\1{str(data["accent"])};', s)
    if 'muted' in data:
        s = re.sub(r'(--muted:\s*)[^;]+;', rf'\1{str(data["muted"])};', s)

    # Update hint text
    if 'hint' in data:
        safe_hint = html.escape(str(data['hint']))
        s = re.sub(r'(<p class="hint">).*?(</p>)', rf'\1{safe_hint}\2', s, flags=re.S)

    # Replace gift list contents
    if 'gifts' in data and isinstance(data['gifts'], list):
        list_items = []
        for g in data['gifts']:
            href = str(g.get('href', '#'))
            text = g.get('text', '')
            # HTML-escape the visible text and the href for safety
            safe_text = html.escape(str(text))
            safe_href = html.escape(href, quote=True)
            list_items.append(
                f'          <li><a href="{safe_href}" target="_blank" rel="noopener">{safe_text}</a></li>'
            )
        list_html = '\n'.join(list_items)
        s = re.sub(r'(<ul id="gift-list"[\s\S]*?>)\s*[\s\S]*?(</ul>)', rf'\1\n{list_html}\n        \2', s, flags=re.S)

    # Update notes paragraph
    if 'notes' in data:
        safe_notes = html.escape(str(data['notes']))
        s = re.sub(r'(<section class="notes">[\s\S]*?<p>).*?(</p>[\s\S]*?</section>)', rf'\1{safe_notes}\2', s, flags=re.S)

    # Ensure the QR placeholder stays empty: do not embed any SVG here.
    # Keep the start/end markers but remove any content between them so the
    # QR injector can add the generated SVG later.
    s = re.sub(
        r'(<!-- QR-PLACEHOLDER-START -->)[\s\S]*?(<!-- QR-PLACEHOLDER-END -->)',
        r'\1\n\2',
        s,
        flags=re.S,
    )

    return s


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=False, help='Path to recipient JSON file (omit with --bulk)')
    parser.add_argument('--template', default='index.html', help='Template HTML file')
    parser.add_argument('--out', help='Output filename (optional)')
    parser.add_argument('--bulk', action='store_true', help='Generate all recipients in a directory')
    parser.add_argument('--recipients-dir', default='recipients', help='Directory containing recipient JSON files when using --bulk')
    args = parser.parse_args()
    tmpl_path = Path(args.template)
    if not tmpl_path.exists():
        print(f'Error: template {tmpl_path} not found')
        return 2

    template_text = tmpl_path.read_text(encoding='utf-8')

    # simple slug helper
    def slugify(name: str) -> str:
        s = name.strip().lower()
        s = re.sub(r"[^a-z0-9\s-]", '', s)
        s = re.sub(r"[\s]+", '-', s)
        return s

    def _write_for_data(d: dict, out_override: str | None = None) -> Path:
        rendered = render_from_template(template_text, d)
        if out_override:
            outp = Path(out_override)
        else:
            recipient = d.get('recipient') or 'output'
            outp = Path(f"{slugify(recipient)}.html")
        outp.write_text(rendered, encoding='utf-8')
        print(f'Wrote {outp}')
        return outp

    # Bulk mode: generate for all JSON files in recipients dir
    if args.bulk:
        recipients_dir = Path(args.recipients_dir)
        if not recipients_dir.exists():
            print(f'No recipients directory found at {recipients_dir}')
            return 2
        json_files = sorted(recipients_dir.glob('*.json'))
        if not json_files:
            print('No recipient JSON files found to generate')
            return 0
        for jf in json_files:
            try:
                d = json.loads(jf.read_text(encoding='utf-8'))
            except Exception as e:
                print(f'Failed to read {jf}: {e}')
                continue
            _write_for_data(d)
        return 0

    # Single-file mode
    if not args.data:
        print('Error: --data is required unless --bulk is specified')
        return 2

    data_path = Path(args.data)
    if not data_path.exists():
        print(f'Error: data file {data_path} not found')
        return 2

    with data_path.open('r', encoding='utf-8') as f:
        data = json.load(f)

    _write_for_data(data, args.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
