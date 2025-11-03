"""Git tag utilities."""

from ..proc import lines


def ls(n=None):
    """Get list of tags sorted by creation date (most recent first).

    Args:
        n: Optional limit on number of tags to return

    Returns:
        List of tag names
    """
    cmd = [
        'git', 'tag',
        '-l',
        '--format=%(refname:short)',
        '--sort=-creatordate',
    ]
    tags = [tag for tag in lines(cmd) if tag]
    if n:
        tags = tags[:n]
    return tags
