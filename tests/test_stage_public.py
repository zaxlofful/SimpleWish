import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
STAGE_SCRIPT = REPO_ROOT / 'scripts' / 'stage_public.py'


def test_stage_public_uses_recipient_manifest(tmp_path):
    recipients = tmp_path / 'recipients'
    recipients.mkdir()
    (recipients / 'elsa.json').write_text('{}', encoding='utf-8')
    (tmp_path / 'index.html').write_text('index', encoding='utf-8')
    (tmp_path / 'elsa.html').write_text('elsa', encoding='utf-8')
    (tmp_path / 'promo.html').write_text('promo', encoding='utf-8')
    public = tmp_path / 'public'
    public.mkdir()
    (public / 'old.html').write_text('old', encoding='utf-8')

    result = subprocess.run(
        [
            sys.executable,
            str(STAGE_SCRIPT),
            '--root',
            str(tmp_path),
            '--recipients-dir',
            str(recipients),
            '--public-dir',
            str(public),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert sorted(path.name for path in public.glob('*.html')) == [
        'elsa.html',
        'index.html',
    ]
    assert (tmp_path / 'promo.html').read_text(encoding='utf-8') == 'promo'
    assert (tmp_path / 'index.html').exists()
    assert (tmp_path / 'elsa.html').exists()


def test_setup_uses_manifest_staging():
    setup = (REPO_ROOT / 'setup.sh').read_text(encoding='utf-8')

    assert 'scripts/stage_public.py' in setup
    assert 'mv -- *.html' not in setup
