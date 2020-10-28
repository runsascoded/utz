
from os.path import dirname, join
from utz.cd import cd


def test_setup_gsmo(mocker):
    cur_dir = dirname(__file__)
    gsmo_dir = join(cur_dir,'data','gsmo')
    with cd(gsmo_dir):
        from utz.setup import setup
        import setuptools
        mocker.patch('setuptools.setup')
        setup()
        setuptools.setup.assert_called_once_with(
            **dict(
                name='gsmo',
                version='0.0.1',
                description='Commonsense Jupyter/Docker/Git integrations.',
                long_description='# gsmo\nCommonsense Jupyter/Docker/Git integrations.\n- mount current directory into a Docker container\n    - pass through Git configs so that commits in the Docker container exist outside it (with correct permissions)\n    - easily configure Python/Linux environment inside container (see [`gsmo.yml`])\n- run a notebook or script [non-interactively](#non-interactive) (and commit results), or [boot a Jupyter server](#jupyter-server) or [Bash shell](#bash-shell) for interactive work\n\n## Usage\n\n### Non-interactive (`run.ipynb`) <a id="non-interactive"></a>\n`gsmo` helps run notebooks and scripts in a reproducible fashion (inside Docker containers), and pass-through changes (especially Git commits) to the host machine:\n\nRunning:\n```bash\ngsmo\n```\nin a project directory will:\n- load configs ([`gsmo.yml`])\n- build a Docker image\n- run a container from that image\n- run the project\'s `run.ipynb` notebook inside that container\n- Git-commit results  \n\n### Interactive <a id="interactive"></a>\n\n#### Jupyter Server <a id="jupyter-server"></a>\nBuild a Docker image from the current directory, and launch a Jupyter server with the current directory mounted (and various Git- and OS-level configs set, so that changes/commits are reflected on the host machine): \n```bash\ngsmo -j\n```\n- runs at a "random" but stable port derived from a hash of the module name\n- easily configure Python/Linux environment using [`gsmo.yml`]\n\n#### Bash shell <a id="bash-shell"></a>\nBuild a Docker image from the current directory, and launch a Bash shell with it mounted (and various Git- and OS-level configs set, so that changes/commits are reflected on the host machine): \n```bash\ngsmo -s\n```\n\n## Module configuration: \n\n### `gsmo.yml` <a id="gsmo-yml"></a>\nWhen you run `gsmo` in a directory, it will look for a `gsmo.yml` file in the current directory with any of the following fields and build a corresponding Docker image:\n\n- `name` (`str`; default: project directory\'s basename): module name; also used as repository for built Docker image\n- `pip` (`str` or `List[str]`): `pip` libraries to install\n- `apt` (`str` or `List[str]`): `apt` libraries to install\n- `env` (`str` or `List[str]`): environment variables to set\n- `group` (`str` or `List[str]`): OS groups to add to the user inside the container\n  - paths are accepted, in which case the group that owns that path will be used\n- `tag` (`str` or `List[str]`): additional Docker tags within `name` repository\n- `mount` (`str` or `List[str]`): Docker mounts, in several convenient formats:\n  - `<path>`: equivalent to `<path>:/<path>`; easily pass local project subdirectories into Docker container, e.g. `home/.bashrc`, `etc/pip.conf`, etc.\n  - standard Docker `<src>:<dst>` syntax is also supported\n  - in all cases, `~` and env vars are expanded \n- `image` (`str`; default: `runsascoded/gsmo`): base Docker image to build from\n- `commit` (`str` or `List[str]`; default: `out` config dir): paths to Git commit after a run (in non-interactive mode)\n- `root` (`bool`; default `False`)\n  - when set, run as `root` inside container\n  - by default, host-machine uid+gid are used\n- `out` (`str`; default `nbs`): directory to write executed notebooks to\n- `dst` (`str`: default `/src`): path inside container to mount current directory to  \n\n### `Dockerfile`\nWhen building the Docker image (in any of the above modes), if a `Dockerfile` is present in the repository, it will be built and used as the base image (and any `gsmo.yml` configs applied on top of it).\n\n[`gsmo.yml`]: #gsmo-yml\n',
                long_description_content_type='text/markdown',
                license=None,
                author='Ryan Williams',
                author_email='ryan@runsascoded.com',
                packages=['gsmo'],
                classifiers=[
                    'Programming Language :: Python :: 3',
                    'Operating System :: OS Independent',
                    # TODO: LICENSE file wasn't actually present in this release; update this test (and corresponding test submodule) to a newer release when possible
                ],
                python_requires='>=3.6',
            )
        )

