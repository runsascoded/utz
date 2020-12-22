from re import match

from ..process import *


def ls(): return lines('git','remote')


LS_REMOTE_LINE_REGEX = '(?P<sha>[0-9a-f]{40})\s+(?:refs/(?P<type>[^/]+)/(?P<name>.*)|(?P<head>HEAD))'
def parse_ls_remote_lines(lns, head=None, tag=None, sha=None, heads=False, tags=False):
    d = {}
    for ln in lns:
        m = match(LS_REMOTE_LINE_REGEX, ln)
        typ = m['type']
        if typ:
            name = m['name']
            if typ not in d:
                d[typ] = {}
            if not sha or m['sha'].startswith(sha):
                d[typ][name] = m['sha']
        elif m['head']:
            if not sha or m['sha'].startswith(sha):
                d['head'] = m['sha']
        else:
            raise ValueError(f'Unexpected `git ls-remote` line: {ln}')

    if head:
        return d.get('heads', {}).get(head)
    if tag:
        return d.get('tags', {}).get(tag)
    if sha:
        r = {}
        for k,v in d.items():
            if k == 'head':
                if v.startswith(sha):
                    r[k] = v
            else:
                typ = { name:id for name,id in v.items() if id.startswith(sha) }
                if typ:
                    r[k] = typ
        d = r
    if heads or tags:
        if heads and tags: return { 'heads': d.get('heads'), 'tags': d.get('tags') }
        elif heads: return d.get('heads')
        elif tags: return d.get('tags')
        else: raise

    return d


def ls_remote(remote, *args, head=None, tag=None, sha=None, heads=False, tags=False):
    cmd = ['git','ls-remote']
    if head or heads: cmd += ['--heads']
    if tag or tags: cmd += ['--tags']
    cmd += (remote,) + args
    lns = lines(cmd)
    return parse_ls_remote_lines(lns, head=head, tag=tag, sha=sha, heads=heads, tags=tags)


def exists(name): return name in ls()


def url(name, *args, **kwargs):
    if not exists(name):
        if len(args) == 1:
            default = args[0]
        elif 'default' in kwargs:
            default = kwargs.pop('default')
        else:
            raise ValueError(f"Remote {name} doesn't exist")

        return default
    
    return line('git','remote','get-url',name)
_url = url


def init(name, url, branch=None, remote_branch=None, fetch=True, checkout=True, push=True):
    if exists(name):
        existing_url = _url(name)
        if existing_url != url:
            run('git','remote','set-url',name,url)
    else:
        run('git','remote','add',name,url)
    
    if fetch:
        run('git','fetch',name)
    
    if branch:
        remote_branch = remote_branch or 'master'
        upstream = f'{name}/{remote_branch}'
        try:
            run('git','branch','-u',upstream,branch)
        except CalledProcessError as e:
            if push:
                print(f'Failed to track upstream branch {upstream}; attempting to push {branch}:{remote_branch}')
                run('git','push',name,f'{branch}:{remote_branch}')
                run('git','branch','-u',upstream,branch)
            else:
                raise e
        if checkout:
            run('git','checkout',branch)


def push(name=None, local=None, remote=None):
    refspec = None
    if local:
        if remote:
            refspec = f'{local}:{remote}'
        else:
            refspec = f'{local}:{local}'
    
    run('git','push',name,refspec)

