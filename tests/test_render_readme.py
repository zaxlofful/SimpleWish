from scripts.render_readme import get_owner_repo, ensure_badge_links


def test_get_owner_repo_from_env(monkeypatch):
    monkeypatch.setenv('GITHUB_REPOSITORY', 'elsa/example')
    owner, repo = get_owner_repo()
    assert owner == 'elsa'
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


def test_get_owner_repo_fallback_no_env(monkeypatch, tmp_path):
    """Test fallback when GITHUB_REPOSITORY is not set.

    With no env var and no valid git remote (we monkeypatch into a temp dir
    that has no .git), the function should still return a two-element tuple
    of non-empty strings rather than raising.
    """
    monkeypatch.delenv('GITHUB_REPOSITORY', raising=False)
    # Run outside any real git repo so the git-remote fallback also fails
    monkeypatch.chdir(str(tmp_path))

    result = get_owner_repo()

    assert isinstance(result, tuple) and len(result) == 2, (
        'get_owner_repo() must return a (owner, repo) tuple'
    )
    owner, repo = result
    assert isinstance(owner, str) and owner.strip(), 'owner must be a non-empty string'
    assert isinstance(repo, str) and repo.strip(), 'repo must be a non-empty string'
