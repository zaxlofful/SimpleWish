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

    def find_alternate_workflow_link(owner, repo, workflow_basename, alt_name=None):
        """Return a workflow link for an existing workflow file.

        Attempts these strategies in order:
        - If `.github/workflows/{workflow_basename}` exists, return its link.
        - Try common mappings (e.g. `test.yml` -> `pytest.yml`).
        - Search `.github/workflows/` for a file whose `name:` matches `alt_name` (case-insensitive).
        - Return None if nothing found.
        """
        workflows_dir = os.path.join('.github', 'workflows')
        if not workflow_basename:
            return None
        candidate_path = os.path.join(workflows_dir, workflow_basename)
        if os.path.exists(candidate_path):
            return f'https://github.com/{owner}/{repo}/actions/workflows/{workflow_basename}'

        # Common mappings
        mappings = {
            'test.yml': 'pytest.yml',
            'test.yaml': 'pytest.yml',
        }
        mapped = mappings.get(workflow_basename)
        if mapped:
            mapped_path = os.path.join(workflows_dir, mapped)
            if os.path.exists(mapped_path):
                return f'https://github.com/{owner}/{repo}/actions/workflows/{mapped}'

        # Try to find a workflow file whose `name:` matches alt_name (case-insensitive)
        if alt_name:
            try:
                for fn in os.listdir(workflows_dir):
                    full = os.path.join(workflows_dir, fn)
                    if not os.path.isfile(full):
                        continue
                    try:
                        with open(full, 'r', encoding='utf-8') as wf:
                            txt = wf.read()
                        # look for a name: line
                        m = re.search(r'^\s*name:\s*["\']?(?P<wname>[^"\']+)["\']?', txt, flags=re.IGNORECASE | re.MULTILINE)
                        if m:
                            wname = m.group('wname').strip().lower()
                            if wname == alt_name.strip().lower():
                                return f'https://github.com/{owner}/{repo}/actions/workflows/{fn}'
                    except Exception:
                        continue
            except Exception:
                pass

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

        # If image URL is a GitHub actions badge for this repo, prefer linking to the workflow page
        if img_url and 'github.com' in img_url and '/actions/workflows/' in img_url and img_parsed == (owner.lower(), repo.lower()):
            # Extract the workflow basename from the badge URL
            mb = re.search(r'/actions/workflows/(?P<wf>[^/]+)(?:/badge\.svg(?:\?.*)?)?$', img_url)
            wf_basename = mb.group('wf') if mb else None
            # alt_name: try to infer from the badge alt text (not available here), so use basename without extension
            alt_name = None
            if wf_basename:
                alt_name = os.path.splitext(wf_basename)[0]

            workflow_link = find_alternate_workflow_link(owner, repo, wf_basename, alt_name) or re.sub(r'/badge\.svg(?:\?.*)?$', '', img_url)
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
            mb = re.search(r'/actions/workflows/(?P<wf>[^/]+)(?:/badge\.svg(?:\?.*)?)?$', img_url)
            wf_basename = mb.group('wf') if mb else None
            alt_name = os.path.splitext(wf_basename)[0] if wf_basename else None
            workflow_link = find_alternate_workflow_link(owner, repo, wf_basename, alt_name) or re.sub(r'/badge\.svg(?:\?.*)?$', '', img_url)
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
