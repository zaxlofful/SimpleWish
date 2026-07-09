import json
import re
from pathlib import Path

import pytest

from scripts.generate_recipient import render_from_template


def test_generate_recipient_from_example():
    repo_root = Path(__file__).resolve().parent.parent
    data_path = repo_root / 'recipients' / 'elsa.json'
    assert data_path.exists()

    data = json.loads(data_path.read_text(encoding='utf-8'))

    template_path = repo_root / 'index.html'
    assert template_path.exists()
    tmpl = template_path.read_text(encoding='utf-8')

    rendered = render_from_template(tmpl, data)

    # QR placeholder should be left empty (start and end markers present, no embedded SVG)
    assert re.search(r'<!-- QR-PLACEHOLDER-START -->\s*\n\s*<!-- QR-PLACEHOLDER-END -->', rendered)

    # Check that the first gift renders as an anchor with the visible text
    assert '<a href="https://example.com/raspberry-pi"' in rendered
    assert 'Raspberry Pi 5 — 8GB RAM starter kit' in rendered

    # Title and recipient should be updated
    assert "<title>Elsa&#x27;s Christmas List</title>" in rendered
    assert 'Christmas List for Elsa' in rendered

    # Notes should be HTML-escaped (ampersand becomes &amp;)
    assert 'Shipping &amp; availability' in rendered


@pytest.mark.parametrize(
    'field',
    ['accent', 'muted', 'qr_foreground', 'qr_background'],
)
def test_render_rejects_non_hex_colors(field):
    template = (
        '<!-- QR metadata: test -->'
        '<style>:root { --accent:#b71c1c; --muted:#6b7280; }</style>'
    )
    data = {
        field: (
            'red; } body::before { '
            'content: url(https://evil.example/collect) }'
        )
    }

    with pytest.raises(ValueError, match=field):
        render_from_template(template, data)


def test_render_drops_javascript_gift_link():
    template = '<ul id="gift-list"><li>placeholder</li></ul>'
    data = {
        'gifts': [
            {
                'text': 'Click me',
                'href': 'javascript:alert(document.cookie)',
            }
        ]
    }

    rendered = render_from_template(template, data)

    assert '<li>Click me</li>' in rendered
    assert 'href=' not in rendered
    assert 'javascript:' not in rendered


def test_render_drops_credentialed_gift_link():
    template = '<ul id="gift-list"><li>placeholder</li></ul>'
    data = {
        'gifts': [
            {
                'text': 'Sneaky link',
                'href': 'https://user:secret@example.com/gift',
            }
        ]
    }

    rendered = render_from_template(template, data)

    assert '<li>Sneaky link</li>' in rendered
    assert 'href=' not in rendered
    assert 'secret' not in rendered
