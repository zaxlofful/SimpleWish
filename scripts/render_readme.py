#!/usr/bin/env python3
import os
import re
import subprocess

OUTPUT = 'README.md'


def get_owner_repo():
    # Prefer GITHUB_REPOSITORY env var (OWNER/REPO)
    gr = os.environ.get('GITHUB_REPOSITORY')
    if gr and '/' in gr:
        return tuple(gr.split('/', 1))
    # Fallback: try git remote
    try:
        out = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], universal_newlines=True).strip()
        # handle git@github.com:owner/repo.git and https://github.com/owner/repo.git
        m = re.search(r'[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$', out)
        if m:
            return m.group('owner'), m.group('repo')
    except Exception:
        pass
    # last resort
    return 'ZaxLofful', 'SimpleWish'


def ensure_badge_links():
    """Ensure standalone markdown images (badges) in README.md are wrapped with a link.

    Example: convert
      ![badge](https://img.shields.io/...)
    to
      [![badge](https://img.shields.io/...)](https://github.com/owner/repo)

    Only images that are NOT already inside a markdown link are changed.
    """
    owner, repo = get_owner_repo()
    repo_url = f'https://github.com/{owner}/{repo}'

    if not os.path.exists(OUTPUT):
        print(f'{OUTPUT} not found; nothing to do')
        return 0

    with open(OUTPUT, 'r', encoding='utf-8') as f:
        content = f.read()

    changes = 0

    def extract_owner_repo_from_url(url):
        m = re.search(r'github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git|/.*)?$', url)
        if m:
            return m.group('owner'), m.group('repo')
        return None

    # 1) Fix links that wrap images but point somewhere else
    linked_pattern = re.compile(r'\[(!\[[^\]]*\]\([^\)]*\))\]\(([^)]*)\)')

    def linked_repl(m):
        nonlocal changes
        img = m.group(1)
        link = m.group(2).strip()
        parsed = extract_owner_repo_from_url(link) if link else None
        if parsed is None:
            # Not a github URL (or empty) -> replace with repo_url
            changes += 1
            return f'[{img}]({repo_url})'
        else:
            cur_owner, cur_repo = parsed
            if cur_owner == owner and cur_repo == repo:
                return m.group(0)  # correct link; leave unchanged
            else:
                # Link points to a different repo -> replace
                changes += 1
                return f'[{img}]({repo_url})'

    content = linked_pattern.sub(linked_repl, content)

    # 2) Wrap standalone images (not already inside a link)
    standalone_pattern = re.compile(r'(?<!\[)(!\[[^\]]*\]\([^\)]*\))')

    def standalone_repl(m):
        nonlocal changes
        changes += 1
        img = m.group(1)
        return f'[{img}]({repo_url})'

    content = standalone_pattern.sub(standalone_repl, content)

    if changes > 0:
        with open(OUTPUT, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Fixed or wrapped {changes} badge(s) to point to {repo_url} in {OUTPUT}')
    else:
        print('No badge link changes required')
    return 0


if __name__ == '__main__':
    raise SystemExit(ensure_badge_links())
