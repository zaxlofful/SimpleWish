import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_python_requirements_are_exact_and_hashed():
    for name in ('requirements.txt', 'requirements-dev.txt'):
        content = (
            REPO_ROOT / 'scripts' / name
        ).read_text(encoding='utf-8')

        # Validate line by line so stray pip options (--index-url,
        # --trusted-host, ...) cannot hide between requirement entries.
        hash_counts = {}
        requirement = None
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if line.endswith('\\'):
                line = line[:-1].strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('--hash=sha256:'):
                assert requirement is not None, (
                    f'{name}: hash before any requirement: {raw_line}'
                )
                hash_counts[requirement] += 1
                continue
            assert not line.startswith('-'), (
                f'{name}: unexpected pip option: {raw_line}'
            )
            specifier = line.split(';', 1)[0].strip()
            assert '==' in specifier, (
                f'{name}: requirement is not exact-pinned: {raw_line}'
            )
            requirement = line
            assert requirement not in hash_counts, (
                f'{name}: duplicate requirement: {raw_line}'
            )
            hash_counts[requirement] = 0

        assert hash_counts, f'{name}: no requirements found'
        for pinned, count in hash_counts.items():
            assert count > 0, f'{name}: missing hash for {pinned}'


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
