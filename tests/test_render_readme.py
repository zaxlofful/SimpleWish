import os
from pathlib import Path
import shutil

from scripts.render_readme import get_owner_repo, ensure_badge_links


def test_get_owner_repo_from_env(monkeypatch):
    monkeypatch.setenv('GITHUB_REPOSITORY', 'alice/example')
    owner, repo = get_owner_repo()
    assert owner == 'alice'
    assert repo == 'example'


def test_ensure_badge_links_wraps_and_links(tmp_path, monkeypatch):
    # Prepare a fake repo layout
    repo_root = tmp_path
    monkeypatch.chdir(str(repo_root))
    monkeypatch.setenv('GITHUB_REPOSITORY', 'owner/repo')

    readme = repo_root / 'README.md'
    # include a standalone shield and a github actions badge that maps to pytest.yml
    content = (
        'Intro\n'
        '![ci badge](https://img.shields.io/some)\n'
        '![tests](https://github.com/owner/repo/actions/workflows/test.yml/badge.svg)\n'
    )
    readme.write_text(content, encoding='utf-8')

    workflows_dir = repo_root / '.github' / 'workflows'
    workflows_dir.mkdir(parents=True)
    # create pytest.yml so mapping from test.yml -> pytest.yml succeeds
    (workflows_dir / 'pytest.yml').write_text('name: pytest\n', encoding='utf-8')

    rc = ensure_badge_links()
    assert rc == 0

    new_content = readme.read_text(encoding='utf-8')
    # standalone badge should be wrapped in a link
    assert new_content.count('](') >= 2
    # the actions badge should now link to the workflow page (pytest.yml)
    assert 'actions/workflows/pytest.yml' in new_content
