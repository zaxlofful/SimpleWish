#!/usr/bin/env python3
"""
Script to detect the latest stable Python version and update all references
in the repository to use it.
"""
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional


def get_latest_python_version() -> Optional[str]:
    """
    Determine the latest stable Python 3.x version by querying Docker Hub
    `library/python` tags (e.g. "3.12-slim").
    Returns a version string like "3.12" or None on failure.
    """
    try:
        # Try to use the Docker Hub API to find available Python versions
        # This is more reliable in CI environments
        result = subprocess.run(
            ['curl', '-s', 'https://registry.hub.docker.com/v2/repositories/library/python/tags?page_size=100'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            print(f"Failed to fetch Docker Hub tags: {result.stderr}")
            return None

        # Parse JSON response
        data = json.loads(result.stdout)

        # Look for tags like "3.12-slim", "3.11-slim", and also patch tags like
        # "3.12.1-slim". We normalize to the major.minor part (e.g. "3.12").
        pattern = r'^(\d+\.\d+)(?:\.\d+)?-slim$'
        versions = []

        for tag_info in data.get('results', []):
            tag_name = tag_info.get('name', '')
            match = re.match(pattern, tag_name)
            if match:
                version = match.group(1)
                # We assume versions 3.8 and above are relevant for this project;
                # the workflow will test compatibility with newer Python 3 releases
                # automatically. Limit to Python 3.x only to prevent automatic
                # adoption of Python 4.x which may have breaking changes.
                major, minor = map(int, version.split('.'))
                if major == 3 and minor >= 8:
                    versions.append(version)

        if not versions:
            print("Could not find Python versions in Docker Hub tags")
            return None

        # Sort and get the highest version
        versions = sorted(set(versions), key=lambda v: tuple(map(int, v.split('.'))))
        latest = versions[-1]
        print(f"Latest stable Python version: {latest}")
        return latest
    except Exception as e:
        print(f"Error getting latest Python version: {e}")
        return None


def get_latest_docker_slim_tag(python_version: str) -> Optional[str]:
    """
    Get the latest Docker slim image tag for the given Python version.
    Returns tag like '3.12-slim' or None on failure.
    """
    # Validate input format
    if not re.match(r'^\d+\.\d+$', python_version):
        print(f"Invalid Python version format: {python_version}")
        return None

    try:
        # Check if docker command is available
        docker_check = subprocess.run(
            ['docker', '--version'],
            capture_output=True,
            timeout=10
        )
        if docker_check.returncode != 0:
            print("Docker is not available in the environment")
            return None

        # Verify the tag exists by trying to pull image metadata
        slim_tag = f"{python_version}-slim"
        result = subprocess.run(
            ['docker', 'manifest', 'inspect', f'python:{slim_tag}'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print(f"Found Docker image: python:{slim_tag}")
            return slim_tag
        else:
            print(f"Docker image python:{slim_tag} not found")
            return None
    except FileNotFoundError:
        print("Docker command not found in PATH")
        return None
    except Exception as e:
        print(f"Error getting Docker slim tag: {e}")
        return None


def update_file_content(
    file_path: Path,
    old_version: str,
    new_version: str,
    old_docker_tag: str,
    new_docker_tag: str
) -> bool:
    """
    Update Python version references in a file.
    Returns True if changes were made, False otherwise.
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        # Update python-version: references in YAML files
        content = re.sub(
            rf"python-version:\s*['\"]?{re.escape(old_version)}['\"]?",
            f"python-version: '{new_version}'",
            content
        )

        # Update FROM python:X.XX-slim in Dockerfiles
        content = re.sub(
            rf"FROM python:{re.escape(old_docker_tag)}",
            f"FROM python:{new_docker_tag}",
            content
        )

        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            print(f"Updated {file_path}")
            return True
        else:
            print(f"No changes needed in {file_path}")
            return False
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False


def get_current_python_version(repo_root: Path) -> Optional[str]:
    """
    Get the current Python version used in the repository.
    Checks the build-ci-image.yml workflow file.
    """
    workflow_file = repo_root / ".github" / "workflows" / "build-ci-image.yml"
    try:
        content = workflow_file.read_text(encoding='utf-8')
        match = re.search(r"python-version:\s*['\"]?(\d+\.\d+)['\"]?", content)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"Error reading current version: {e}")
    return None


def main():
    """Main function to update Python and Docker versions."""
    repo_root = Path(__file__).parent.parent

    # Get current version
    current_version = get_current_python_version(repo_root)
    if not current_version:
        print("Error: Could not determine current Python version")
        sys.exit(1)

    print(f"Current Python version: {current_version}")
    current_docker_tag = f"{current_version}-slim"

    # Get latest version
    latest_version = get_latest_python_version()
    if not latest_version:
        print("Error: Could not determine latest Python version")
        sys.exit(1)

    # Check if update is needed
    if latest_version == current_version:
        print(f"Already using latest Python version: {current_version}")
        sys.exit(0)

    print(f"Update available: {current_version} -> {latest_version}")

    # Get latest Docker slim tag
    latest_docker_tag = get_latest_docker_slim_tag(latest_version)
    if not latest_docker_tag:
        print("Error: Could not verify Docker slim image availability")
        sys.exit(1)

    # Files to update
    files_to_update = [
        repo_root / ".github" / "ci" / "Dockerfile.infra",
        repo_root / ".github" / "ci" / "Dockerfile.qr",
        repo_root / ".github" / "workflows" / "build-ci-image.yml",
        repo_root / ".github" / "workflows" / "check-todo.yml",
    ]

    # Update files
    changes_made = False
    failed_files = []
    for file_path in files_to_update:
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            failed_files.append(str(file_path))
            continue
        
        result = update_file_content(
            file_path,
            current_version,
            latest_version,
            current_docker_tag,
            latest_docker_tag
        )
        if result:
            changes_made = True
        else:
            # Check if file still contains the exact old patterns (update failed)
            # Use word boundaries and specific patterns to avoid false positives
            try:
                content = file_path.read_text(encoding='utf-8')
                # Check for old version patterns that should have been replaced
                old_version_pattern = rf"python-version:\s*['\"]?{re.escape(current_version)}['\"]?"
                old_docker_pattern = rf"FROM python:{re.escape(current_docker_tag)}"
                
                if re.search(old_version_pattern, content) or re.search(old_docker_pattern, content):
                    print(f"Error: Failed to update {file_path} - old version patterns still present")
                    failed_files.append(str(file_path))
            except Exception as e:
                print(f"Error checking {file_path}: {e}")
                failed_files.append(str(file_path))

    if failed_files:
        print(f"\nError: Failed to update the following files: {', '.join(failed_files)}")
        sys.exit(1)

    if changes_made:
        print("\nSuccessfully updated Python version references")
        print(f"Updated from {current_version} to {latest_version}")
        sys.exit(0)
    else:
        print("\nNo changes were made")
        sys.exit(1)


if __name__ == "__main__":
    main()
