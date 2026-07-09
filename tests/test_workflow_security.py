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
            if reference.startswith(('./', '../')):
                # Local actions ship with the repository; there is no
                # external revision to pin.
                continue
            _, separator, revision = reference.rpartition('@')
            if reference.startswith('docker://'):
                pinned = separator and re.fullmatch(
                    r'sha256:[0-9a-f]{64}', revision
                )
            else:
                pinned = separator and re.fullmatch(
                    r'[0-9a-f]{40}', revision
                )
            if not pinned:
                unpinned.append(f'{workflow.name}: {reference}')

    assert unpinned == []


def test_trivy_does_not_receive_docker_socket():
    workflow = (
        WORKFLOWS_DIR / 'build-ci-image.yml'
    ).read_text(encoding='utf-8')

    assert '/var/run/docker.sock' not in workflow
    assert 'aquasecurity/trivy:latest' not in workflow
    assert re.search(
        r'ghcr\.io/aquasecurity/trivy@sha256:[0-9a-f]{64}',
        workflow,
    )


def test_ci_does_not_execute_mutable_container_tags():
    mutable_images = []
    for workflow in sorted(WORKFLOWS_DIR.glob('*.yml')):
        content = workflow.read_text(encoding='utf-8')
        if re.search(r'^\s*image:.*:main\s*$', content, re.MULTILINE):
            mutable_images.append(workflow.name)

    assert mutable_images == []


def test_pr_checks_do_not_receive_issue_write_permission():
    for name in ('lint.yml', 'pytest.yml'):
        workflow = (WORKFLOWS_DIR / name).read_text(encoding='utf-8')
        check_job = workflow.split('\n  report-', 1)[0]

        assert 'container:' not in check_job
        assert 'issues: write' not in check_job
        assert 'contents: read' in check_job
        assert 'persist-credentials: false' in check_job


def test_qr_change_output_is_single_line():
    workflow = (
        WORKFLOWS_DIR / 'generate-qrs.yml'
    ).read_text(encoding='utf-8')

    assert 'CHANGED=$(git status --porcelain)' not in workflow
