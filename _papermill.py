#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from inspect import getfullargspec
import json
from jupyter_client import kernelspec
from papermill import execute_notebook
from sys import executable
from ._collections import singleton


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


def execute(input, output=None, nest_asyncio=True, *args, **kwargs):
    output = output or input
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

    print(f'parameters: {parameters}')
    execute_notebook(
        str(input),
        str(output),
        *args,
        nest_asyncio=nest_asyncio,
        **exec_kwargs,
        parameters=parameters,
    )

