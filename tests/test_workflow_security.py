import re
from pathlib import Path


WORKFLOWS_DIR = (
    Path(__file__).resolve().parent.parent / '.github' / 'workflows'
)


def test_workflow_actions_are_pinned_to_commit_shas():
    unpinned = []
    for workflow in sorted(WORKFLOWS_DIR.glob('*.yml')):
        content = workflow.read_text(encoding='utf-8')
        for reference in re.findall(
            r'^\s*uses:\s*([^\s#]+)',
            content,
            flags=re.MULTILINE,
        ):
            _, separator, revision = reference.rpartition('@')
            if not separator or not re.fullmatch(r'[0-9a-f]{40}', revision):
                unpinned.append(f'{workflow.name}: {reference}')

    assert unpinned == []
