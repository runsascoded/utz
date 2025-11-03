"""GitHub Gist operations for uploading files and managing gist repositories."""
from __future__ import annotations

import re
import shutil
import tempfile
from os import chdir
from pathlib import Path
from urllib.parse import quote

from utz import proc, err


def get_github_user() -> str | None:
    """Get the current GitHub username."""
    try:
        return proc.line('gh', 'api', 'user', '--jq', '.login', log=False)
    except Exception:
        return None


def get_gist_remote_name(gist_id: str) -> str:
    """Find the remote name for a gist repository."""
    try:
        remotes = proc.lines('git', 'remote', log=False)
        for remote in remotes:
            if not remote:
                continue
            try:
                url = proc.line('git', 'remote', 'get-url', remote, err_ok=True, log=False)
                if url and (f'gist.github.com:{gist_id}' in url or f'gist.github.com/{gist_id}' in url):
                    return remote
            except Exception:
                continue
    except Exception:
        pass
    return 'origin'


def create_gist(description: str = "Image assets", content: str = "# Image Assets\nThis gist stores image assets.\n") -> str | None:
    """Create a new gist and return its ID."""
    try:
        output = proc.text('gh', 'gist', 'create', '--desc', description, '-', input=content.encode(), log=False)
        if not output:
            return None

        # Extract gist ID from URL
        match = re.search(r'gist\.github\.com/([a-f0-9]+)', output)
        if match:
            return match.group(1)
    except Exception as e:
        err(f"Error creating gist: {e}")
    return None


def upload_files_to_gist(
    files: list[tuple[str, str]],
    gist_id: str,
    branch: str = 'assets',
    is_local_clone: bool = False,
    commit_msg: str | None = None,
    verbose: bool = True,
    remote_name: str | None = None,
) -> list[tuple[str, str, str]]:
    """Upload files to a gist branch.

    Args:
        files: List of (source_path, target_name) tuples
        gist_id: Gist ID to upload to
        branch: Branch name (default: 'assets')
        is_local_clone: True if we're already in a clone of this gist
        commit_msg: Custom commit message (optional)
        verbose: Print progress messages
        remote_name: Name of the remote (auto-detected if not provided)

    Returns:
        List of (original_name, safe_name, url) tuples
    """
    if not gist_id:
        err("Error: No gist ID provided")
        return []

    # Get GitHub username
    user = get_github_user()
    if not user:
        err("Error: Could not determine GitHub username")
        return []

    # Prepare file mappings
    file_mapping = []
    for source_path, target_name in files:
        if not Path(source_path).exists():
            err(f"Error: File not found: {source_path}")
            continue
        file_mapping.append((source_path, target_name, target_name))

    if not file_mapping:
        return []

    results = []

    if is_local_clone:
        # We're already in the gist repo
        temp_dir = tempfile.mkdtemp(prefix='assets_')

        if not remote_name:
            remote_name = get_gist_remote_name(gist_id)
            if verbose:
                err(f"Using remote '{remote_name}'")

        try:
            # Copy files to temp directory
            temp_files = []
            for source_path, orig_name, safe_name in file_mapping:
                temp_path = Path(temp_dir) / safe_name
                shutil.copy2(source_path, temp_path)
                temp_files.append((orig_name, safe_name, temp_path))
                if verbose:
                    err(f"Staged {orig_name}")

            # Check if branch exists on remote
            try:
                output = proc.text('git', 'ls-remote', '--heads', remote_name, branch, err_ok=True, log=False)
                branch_exists = bool(output.strip() if output else False)
            except Exception:
                branch_exists = False

            if branch_exists:
                proc.run('git', 'fetch', remote_name, f'{branch}:{branch}', log=False)
                if verbose:
                    err(f"Fetched existing branch '{branch}'")
                parent_ref = branch
            else:
                if verbose:
                    err(f"Creating new branch '{branch}'")
                parent_ref = None

            # Build tree with all files
            tree_entries = []

            # Get existing tree if we have a parent
            if parent_ref:
                try:
                    existing_tree = proc.text('git', 'ls-tree', parent_ref, err_ok=True, log=False)
                    if existing_tree:
                        new_files = {safe_name for _, safe_name, _ in temp_files}
                        for line in existing_tree.strip().split('\n'):
                            if line:
                                parts = line.split('\t', 1)
                                if len(parts) == 2:
                                    filename = parts[1]
                                    if filename not in new_files:
                                        tree_entries.append(line)
                except Exception:
                    pass

            # Add new/updated files
            for orig_name, safe_name, temp_path in temp_files:
                blob_hash = proc.line('git', 'hash-object', '-w', str(temp_path), log=False)
                tree_entries.append(f'100644 blob {blob_hash}\t{safe_name}')

            # Create tree - use proc.line with input parameter
            tree_input = '\n'.join(tree_entries) + '\n'
            tree_hash = proc.line('git', 'mktree', input=tree_input.encode(), log=False)

            # Create commit
            if not commit_msg:
                commit_msg = 'Add assets'
            commit_cmd = ['git', 'commit-tree', tree_hash, '-m', commit_msg]
            if parent_ref:
                commit_cmd.extend(['-p', parent_ref])
            commit_hash = proc.line(*commit_cmd, log=False)

            # Update branch ref
            proc.run('git', 'update-ref', f'refs/heads/{branch}', commit_hash, log=False)

            # Push the branch
            proc.run('git', 'push', remote_name, f'{branch}:{branch}', log=False)
            if verbose:
                err(f"Pushed to branch '{branch}'")

            # Build results with commit SHA
            for orig_name, safe_name, _ in temp_files:
                encoded_name = quote(safe_name)
                url = f"https://gist.githubusercontent.com/{user}/{gist_id}/raw/{commit_hash}/{encoded_name}"
                results.append((orig_name, safe_name, url))
                if verbose:
                    err(f"Uploaded: {url}")

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    else:
        # Need to clone the gist
        temp_dir = tempfile.mkdtemp(prefix='gist_')
        original_dir = Path.cwd()

        try:
            gist_url = f"git@gist.github.com:{gist_id}.git"
            proc.run('git', 'clone', gist_url, temp_dir, log=False)
            chdir(temp_dir)

            # Create or switch to branch
            try:
                proc.run('git', 'checkout', '-b', branch, log=False)
                if verbose:
                    err(f"Created branch '{branch}'")
            except Exception:
                try:
                    proc.run('git', 'checkout', branch, log=False)
                    if verbose:
                        err(f"Using existing branch '{branch}'")
                except Exception:
                    if verbose:
                        err(f"Warning: Could not checkout branch '{branch}', using main")
                    branch = 'main'

            # Copy and add files
            for source_path, orig_name, safe_name in file_mapping:
                shutil.copy2(source_path, safe_name)
                proc.run('git', 'add', safe_name, log=False)
                if verbose:
                    err(f"Added {orig_name}")

            # Commit and push
            if not commit_msg:
                commit_msg = 'Add assets'
            proc.run('git', 'commit', '-m', commit_msg, log=False)
            proc.run('git', 'push', 'origin', branch, log=False)

            # Get the commit hash for the URL
            commit_hash = proc.line('git', 'rev-parse', 'HEAD', log=False)

            # Build results with commit SHA
            for _, orig_name, safe_name in file_mapping:
                encoded_name = quote(safe_name)
                url = f"https://gist.githubusercontent.com/{user}/{gist_id}/raw/{commit_hash}/{encoded_name}"
                results.append((orig_name, safe_name, url))
                if verbose:
                    err(f"Uploaded: {url}")

        finally:
            chdir(original_dir)
            shutil.rmtree(temp_dir, ignore_errors=True)

    return results


def format_upload_output(
    filename: str,
    url: str,
    format_type: str = 'auto',
    alt_text: str | None = None,
) -> str:
    """Format the output based on file type and format preference.

    Args:
        filename: Original filename
        url: URL to the file
        format_type: 'url', 'markdown', 'img', or 'auto'
        alt_text: Alt text for markdown/img formats

    Returns:
        Formatted string
    """
    if not alt_text:
        alt_text = filename

    # Determine output format
    output_format = format_type
    if format_type == 'auto':
        ext = Path(filename).suffix.lower()
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.bmp'}

        if ext in image_extensions:
            output_format = 'markdown'
        else:
            import mimetypes
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type and mime_type.startswith('image/'):
                output_format = 'markdown'
            else:
                output_format = 'url'

    if output_format == 'url':
        return url
    elif output_format == 'markdown':
        return f'![{alt_text}]({url})'
    elif output_format == 'img':
        return f'<img alt="{alt_text}" src="{url}" />'
    else:
        return url
