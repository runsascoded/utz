from subprocess import CalledProcessError
from sys import stderr

from ..proc import *
from . import diff


def resolve_remote_ref(current_branch=None, current_sha=None, verbose=True):
    """
    Resolve which remote ref to use based on current branch and SHA.

    Returns:
        tuple: (ref_name, remote_ref) where ref_name is the branch name to use
               and remote_ref is the full remote reference (e.g., 'origin/branch')
        (None, None) if no ref can be determined

    Raises:
        SystemExit: If multiple remote refs match and are ambiguous
    """
    try:
        # Get current branch and SHA if not provided
        if current_branch is None:
            current_branch = line('git', 'rev-parse', '--abbrev-ref', 'HEAD')
        if current_sha is None:
            current_sha = line('git', 'rev-parse', 'HEAD')

        # Get remote branches that match
        remote_refs = lines('git', 'branch', '-r', '--format=%(refname:short)')
        matching_refs = [r for r in remote_refs if r.endswith(f'/{current_branch}')]

        if len(matching_refs) == 1:
            # Extract the actual branch name from the remote ref
            remote_ref = matching_refs[0]
            # Split "remote/branch" and take the branch part
            ref = remote_ref.split('/', 1)[1] if '/' in remote_ref else remote_ref
            if verbose:
                stderr.write(f"Using ref: {ref} (from remote {remote_ref})\n")
            return ref, remote_ref

        elif len(matching_refs) > 1:
            # Multiple matches - check which one points to the same SHA
            matching_sha_refs = []
            for remote_ref in matching_refs:
                try:
                    remote_sha = line('git', 'rev-parse', remote_ref)
                    if remote_sha == current_sha:
                        matching_sha_refs.append(remote_ref)
                except:
                    pass

            if len(matching_sha_refs) == 1:
                # Exactly one remote ref points to the same SHA
                remote_ref = matching_sha_refs[0]
                ref = remote_ref.split('/', 1)[1] if '/' in remote_ref else remote_ref
                if verbose:
                    stderr.write(f"Using ref: {ref} (from remote {remote_ref} - matches current SHA)\n")
                return ref, remote_ref

            elif len(matching_sha_refs) > 1:
                # Multiple refs point to the same SHA - check if current branch has a tracking branch
                try:
                    upstream = line('git', 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}')
                    # Convert format like 'gh/main' to match remote_ref format
                    if upstream in matching_sha_refs:
                        remote_ref = upstream
                        ref = remote_ref.split('/', 1)[1] if '/' in remote_ref else remote_ref
                        if verbose:
                            stderr.write(f"Using ref: {ref} (from tracking branch {remote_ref})\n")
                        return ref, remote_ref
                except:
                    pass

                # Still ambiguous after checking tracking branch
                stderr.write(f"Error: Multiple remote refs match current branch '{current_branch}' and SHA:\n")
                for r in matching_sha_refs:
                    stderr.write(f"  - {r}\n")
                stderr.write("Please specify --ref explicitly\n")
                exit(1)

            else:
                # No remote refs match the current SHA
                if verbose:
                    stderr.write(f"Warning: Multiple remote refs match branch name '{current_branch}' but none match current SHA:\n")
                    for r in matching_refs:
                        stderr.write(f"  - {r}\n")
                    stderr.write("Using local branch name as ref\n")
                return current_branch, None

        elif current_branch != 'HEAD':
            # No remote matches, but we're on a real branch - use it anyway
            if verbose:
                stderr.write(f"Using ref: {current_branch} (current branch, no remote match)\n")
            return current_branch, None

        else:
            # Detached HEAD with no matches
            return None, None

    except Exception as e:
        # If anything fails, return None
        if verbose:
            stderr.write(f"Warning: Failed to resolve remote ref: {e}\n")
        return None, None


def mv(old, new, untracked=False, checkout=False):
    if current() == old:
        if diff.exists(untracked=untracked):
            raise ValueError(f"Local changes found; refusing to reset --hard")
        else:
            run('git','reset','--hard',new)
    else:
        run('git','branch','-f',old,new)

    if checkout:
        run('git','checkout',new)

def ls():
    return lines('git','for-each-ref','--format=%(refname:short)','refs/heads')
        
def exists(name):
    return check('git','show-ref','--verify','--quiet',f'refs/heads/{name}')

def current(sha_ok=False):
    if sha_ok:
        try:
            return line('git','symbolic-ref','-q','--short','HEAD')
        except CalledProcessError:
            return line('git','log','--no-walk','--format=%h')
    elif sha_ok is None:
        return line('git','symbolic-ref','-q','--short','HEAD', err_ok=True)
    else:
        return line('git','symbolic-ref','-q','--short','HEAD')

