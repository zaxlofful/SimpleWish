import json
from pathlib import Path


REQUIRED_TOP_LEVEL = {"recipient", "title", "gifts"}


def test_recipient_json_files_well_formed_and_have_required_fields():
    repo_root = Path(__file__).resolve().parent.parent
    recipients_dir = repo_root / 'recipients'
    assert recipients_dir.exists(), 'recipients/ directory missing'

    json_files = sorted(recipients_dir.glob('*.json'))
    assert json_files, 'No recipient JSON files found'

    for jf in json_files:
        # ensure each file is valid JSON
        try:
            data = json.loads(jf.read_text(encoding='utf-8'))
        except Exception as e:
            raise AssertionError(f'Failed to parse {jf}: {e}')

        # check required top-level keys
        missing = REQUIRED_TOP_LEVEL - set(data.keys())
        assert not missing, f'{jf.name} is missing required keys: {missing}'

        # recipient and title should be non-empty strings
        assert isinstance(data.get('recipient'), str) and data.get('recipient').strip(), f'{jf.name}: recipient must be a non-empty string'
        assert isinstance(data.get('title'), str) and data.get('title').strip(), f'{jf.name}: title must be a non-empty string'

        # gifts must be a non-empty list
        gifts = data.get('gifts')
        assert isinstance(gifts, list), f'{jf.name}: gifts must be a list'
        assert gifts, f'{jf.name}: gifts list must not be empty'

        for i, g in enumerate(gifts, start=1):
            assert isinstance(g, dict), f'{jf.name}: gift #{i} must be an object'
            # each gift requires a visible text
            text = g.get('text')
            assert isinstance(text, str) and text.strip(), f"{jf.name}: gift #{i} missing or empty 'text'"
            # if href is present it must be a non-empty string
            if 'href' in g:
                href = g.get('href')
                assert isinstance(href, str) and href.strip(), f"{jf.name}: gift #{i} has invalid 'href'"

        # Optional QR-related fields, if present, should be strings or booleans (for qr_decorate)
        for opt in ('qr_foreground', 'qr_background', 'qr_decor_type', 'qr_tree_style', 'qr_decorate'):
            if opt in data:
                val = data[opt]
                assert isinstance(val, (str, bool)), f"{jf.name}: optional field '{opt}' must be a string or boolean"
