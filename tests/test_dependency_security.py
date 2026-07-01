import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_python_requirements_are_exact_and_hashed():
    for name in ('requirements.txt', 'requirements-dev.txt'):
        content = (
            REPO_ROOT / 'scripts' / name
        ).read_text(encoding='utf-8')
        entries = re.split(r'(?m)(?=^[A-Za-z0-9])', content)
        entries = [entry for entry in entries if entry.strip()]

        assert entries
        for entry in entries:
            requirement = entry.splitlines()[0]
            assert '==' in requirement
            assert '--hash=sha256:' in entry


def test_automation_requires_hashes_without_upgrading_pip():
    paths = [
        REPO_ROOT / 'setup.sh',
        REPO_ROOT / '.github' / 'ci' / 'Dockerfile.infra',
        REPO_ROOT / '.github' / 'ci' / 'Dockerfile.qr',
        *sorted((REPO_ROOT / '.github' / 'workflows').glob('*.yml')),
    ]

    for path in paths:
        content = path.read_text(encoding='utf-8')
        assert not re.search(
            r'pip\s+install[^\n]*--upgrade\s+pip',
            content,
        ), path
        for line in content.splitlines():
            if re.search(r'\bpip\s+install\b', line):
                assert '--require-hashes' in line, f'{path}: {line}'
