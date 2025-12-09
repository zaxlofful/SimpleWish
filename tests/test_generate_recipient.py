import json
import re
from pathlib import Path

from scripts.generate_recipient import render_from_template


def test_generate_recipient_from_example():
    repo_root = Path(__file__).resolve().parent.parent
    data_path = repo_root / 'recipients' / 'alice.json'
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
    assert "<title>Alice&#x27;s Christmas List</title>" in rendered
    assert 'Christmas List for Alice' in rendered

    # Notes should be HTML-escaped (ampersand becomes &amp;)
    assert 'Shipping &amp; availability' in rendered
