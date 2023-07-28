#!/usr/bin/env python
from utz import process
from utz.git.repo import git_repo


def ls():
    return process.lines('git', 'submodule', 'foreach', '--quiet', 'echo $name')


def exists(name):
    return name in ls()


def add(url, path=None):
    if exists(path):
        return
    cmd = ['git', 'submodule', 'add', 'url']
    if path:
        cmd.append(path)
    process.run(cmd)


_submodule_map = None


def git_submodules():
    global _submodule_map
    if not _submodule_map:
        _submodule_map = { s.path: s for s in git_repo().submodules }
    return _submodule_map
