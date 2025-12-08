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
        m = re.search(r'github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git|/.*)?$', url, flags=re.IGNORECASE)
        if m:
            return m.group('owner').lower(), m.group('repo').lower()
        return None

    # 1) Fix links that wrap images but point somewhere else
    linked_pattern = re.compile(r'\[(!\[[^\]]*\]\([^\)]*\))\]\(([^)]*)\)')

    def linked_repl(m):
        nonlocal changes
        img = m.group(1)
        link = m.group(2).strip()
        # If the image URL contains a GitHub workflow badge for this repo, prefer linking to the workflow page
        im = re.search(r'!\[[^\]]*\]\(([^\)]+)\)', img)
        img_url = im.group(1).strip() if im else ''
        img_parsed = extract_owner_repo_from_url(img_url) if img_url else None

        # If image URL is a GitHub actions badge for this repo, link to the workflow page (drop /badge.svg)
        if img_url and 'github.com' in img_url and '/actions/workflows/' in img_url and img_parsed == (owner.lower(), repo.lower()):
            workflow_link = re.sub(r'/badge\.svg(?:\?.*)?$', '', img_url)
            if link != workflow_link:
                changes += 1
                return f'[{img}]({workflow_link})'
            return m.group(0)

        parsed = extract_owner_repo_from_url(link) if link else None
        if parsed is None:
            # Not a github URL (or empty) -> leave as-is (non-destructive)
            return m.group(0)
        else:
            cur_owner, cur_repo = parsed
            # compare case-insensitively
            if cur_owner == owner.lower() and cur_repo == repo.lower():
                return m.group(0)  # correct link; leave unchanged
            else:
                # Link points to a different repo -> replace with canonical repo root
                changes += 1
                return f'[{img}]({repo_url})'

    content = linked_pattern.sub(linked_repl, content)

    # 2) Wrap standalone images (not already inside a link)
    standalone_pattern = re.compile(r'(?<!\[)(!\[[^\]]*\]\([^\)]*\))')

    def standalone_repl(m):
        nonlocal changes
        img = m.group(1)
        im = re.search(r'!\[[^\]]*\]\(([^\)]+)\)', img)
        img_url = im.group(1).strip() if im else ''
        img_parsed = extract_owner_repo_from_url(img_url) if img_url else None
        # If it's a GitHub actions badge for this repo, link to the workflow page
        if img_url and 'github.com' in img_url and '/actions/workflows/' in img_url and img_parsed == (owner.lower(), repo.lower()):
            workflow_link = re.sub(r'/badge\.svg(?:\?.*)?$', '', img_url)
            changes += 1
            return f'[{img}]({workflow_link})'
        # Otherwise link to repo root
        changes += 1
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
