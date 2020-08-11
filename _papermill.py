#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from inspect import getfullargspec
import json
from jupyter_client import kernelspec
from os import makedirs
from os.path import abspath, basename, dirname, exists, isdir, join, sep, splitext
from papermill import execute_notebook
from sys import executable
from ._collections import singleton
from . import _git as git
from .process import line, run


def current_kernel():
    kernels = kernelspec.find_kernel_specs()
    kernel = singleton(
        [ 
            name
            for name, kernel_dir
            in kernels.items()
            if json.load(open(f'{kernel_dir}/kernel.json','r'))['argv'][0] == executable
        ], empty_ok=True
    )
    if kernel: return kernel
    return singleton(kernels.keys())


def execute(input, output=None, nest_asyncio=True, cwd=False, inject_paths=False, commit=True, msg=None, start_sha=None, *args, **kwargs):
    if not exists(input) and not input.endswith('.ipynb'):
        input += '.ipynb'
    if not exists(input):
        raise ValueError(f"Nonexistent input notebook: {input}")
    if commit:
        if not start_sha:
            start_sha = git.head.sha()
    name = splitext(input)[0]
    if output:
        if not output.endswith('.ipynb'):
            output = join(output, basename(input))
        out_dir = dirname(abspath(output))
        makedirs(out_dir, exist_ok=True)
    else:
        output = input
    spec = getfullargspec(execute_notebook)
    exec_kwarg_names = spec.args[-len(spec.defaults):]
    exec_kwargs = { 
        name: kwargs.pop(name)
        for name in exec_kwarg_names
        if name in kwargs
    }
    if 'kernel' in kwargs:
        kernel_name = kwargs.pop('kernel')
        if 'kernel_name' in exec_kwargs:
            if exec_kwargs['kernel_name'] != kernel_name:
                raise ValueError(f'Conflicting kernel_name values: {exec_kwargs["kernel_name"]} vs. {kernel_name}')
        else:
            exec_kwargs['kernel_name'] = kernel_name
    else:
        if 'kernel_name' not in exec_kwargs:
            kernel_name = current_kernel()
            exec_kwargs['kernel_name'] = kernel_name

    if 'parameters' in exec_kwargs:
        parameters = exec_kwargs.pop('parameters')
        if kwargs:
            raise ValueError(f'Passing `parameters` arg to papermill, but found dangling kwargs: {kwargs}')
    else:
        parameters = kwargs

    if cwd:
        if cwd is True:
            cwd = None
    else:
        cwd = dirname(abspath(input))
    execute_notebook(
        str(input),
        str(output),
        *args,
        nest_asyncio=nest_asyncio,
        cwd=cwd,
        inject_paths=inject_paths,
        **exec_kwargs,
        parameters=parameters,
    )
    if commit:
        if commit is True:
            commit = []
        elif isinstance(commit, str):
            commit = [commit]
        commit += [output]
        msg = msg or output
        last_sha = git.head.sha()
        run(['git','add'] + commit)
        run('git','commit','-m',msg)
        if start_sha != last_sha:
            repo = git.Repo()
            tree = repo.tree().hexsha
            head = line('git','commit-tree',tree,'-p',start_sha,'-p',last_sha,'-m',msg)
            run('git','reset',head)
