from unittest.mock import patch
from utz import cd, dirname, join, line, match
from utz.version import VERSION_TAG_REGEX, pkg_version


def test_setup_gsmo():
    cur_dir = dirname(__file__)
    gsmo_dir = join(cur_dir,'data','gsmo')
    with cd(gsmo_dir):
        from utz.setup import setup
        import setuptools
        with patch.object(setuptools, 'setup', return_value=None) as mock_setup:
            setup()

        mock_setup.assert_called_once_with(
            **{
                'name': 'gsmo',
                'version': '0.1.1rc2',
                'description': 'Commonsense Jupyter/Docker/Git integrations.',
                'long_description': '# gsmo\nCommonsense Jupyter/Docker/Git integrations.\n\n`gsmo` streamlines mounting and working with Git repositories in Docker containers.\n\nA purpose-built Docker image+container are created (see [`gsmo.yml`] for configuration options), and Git configs are embedded so that commits inside the Docker container exist outside it (with correct permissions, authorship info, etc.).\n\nLocal notebooks or scripts can be executed [non-interactively](#non-interactive) (with results automatically committed to Git), or a [Jupyter server](#jupyter-server) or [Bash shell](#bash-shell) can be booted for interactive work.\n\n## Usage\n\n### `gsmo run`: execute notebooks non-interactively <a id="non-interactive"></a>\n`gsmo` helps run notebooks and scripts in a reproducible fashion (inside Docker containers), and pass-through changes (especially Git commits) to the host machine:\n\nRunning:\n```bash\ngsmo run\n```\nin a project directory will:\n- load configs ([`gsmo.yml`])\n- build a Docker image\n- run a container from that image\n- run the project\'s `run.ipynb` notebook inside that container\n- Git-commit results  \n\n### Interactive <a id="interactive"></a>\n\n#### Jupyter Server <a id="jupyter-server"></a>\nBuild a Docker image from the current directory, and launch a Jupyter server with the current directory mounted (and various Git- and OS-level configs set, so that changes/commits are reflected on the host machine):\n```bash\ngsmo jupyter  # or: gsmo j\n```\n- runs at a "random" but stable port (derived from a hash of the module name)\n- easily configure Python/Linux environment using [`gsmo.yml`]\n\n#### Bash shell <a id="bash-shell"></a>\nBuild a Docker image from the current directory, and launch a Bash shell with it mounted (and various Git- and OS-level configs set, so that changes/commits are reflected on the host machine):\n```bash\ngsmo sh\n```\n\n## Module configuration: \n\n### `gsmo.yml` <a id="gsmo-yml"></a>\nWhen you run `gsmo` in a directory, it will look for a `gsmo.yml` file in the current directory with any of the following fields and build a corresponding Docker image:\n\n#### Docker configs\n- `name` (`str`; default: project directory\'s basename): module name; also used as repository for built Docker image\n- `pip` (`str` or `List[str]`): `pip` libraries to install\n- `apt` (`str` or `List[str]`): `apt` libraries to install\n- `env` (`str` or `List[str]`): environment variables to set\n- `env_file` (`str`): file with environment variables\n- `group` (`str` or `List[str]`): OS groups to add to the user inside the container\n  - paths are accepted, in which case the group that owns that path will be used\n- `tag` (`str` or `List[str]`): additional Docker tags within `name` repository\n- `mount` (`str` or `List[str]`): Docker mounts, in several convenient formats:\n  - `<path>`: equivalent to `<path>:/<path>`; easily pass local project subdirectories into Docker container, e.g. `home/.bashrc`, `etc/pip.conf`, etc.\n  - standard Docker `<src>:<dst>` syntax is also supported\n  - in all cases, `~` and env vars are expanded \n- `image` (`str`; default: `runsascoded/gsmo:<gsmo version>`): base Docker image to build from; `<gsmo version>` will be the pip version of `gsmo` that was installed\n- `root` (`bool`; default `False`)\n  - when set, run as `root` inside container\n  - by default, host-machine uid+gid are used\n- `dst` (`str`: default `/src`): path inside container to mount current directory to  \n\n#### `gsmo run` configs\nThese configs are passed into the Docker container / pertain to the running of a script or notebook inside the container (see [non-interactive mode](#non-interactive)):\n- `run` (`str`; default: `run.ipynb`): notebook to run\n- `dir` (`str`; default: current directory): resolve paths (incl. mounts) relative to this directory\n- `yaml` (`str` or `List[str]`): YAML string(s) with configuration settings for the module being run\n- `yaml_path` (`str` or `List[str]`): YAML file(s) with configuration settings for the module being run\n- `commit` (`str` or `List[str]`; default: `out` config dir): paths to Git commit after a run (in non-interactive mode)\n- `out` (`str`; default `nbs`): directory to write executed notebooks to\n\n#### `gsmo jupyter` configs\n\n### `Dockerfile`\nWhen building the Docker image (in any of the above modes), if a `Dockerfile` is present in the repository, it will be built and used as the base image (and any `gsmo.yml` configs applied on top of it).\n\n[`gsmo.yml`]: #gsmo-yml\n',
                'long_description_content_type': 'text/markdown',
                'install_requires': 'pytz\n',
                # TODO: LICENSE file wasn't actually present in this release; update this test (and corresponding test submodule) to a newer release when possible
                'license': None,
                'author': 'Ryan Williams',
                'author_email': 'ryan@runsascoded.com',
                'packages': ['gsmo', 'gsmo.util'],
                'classifiers': ['Programming Language :: Python :: 3', 'Operating System :: OS Independent'],
                'python_requires': '>=3.9',
            }
        )


def test_parse_version():
    def parse(version):
        return match(VERSION_TAG_REGEX, version).groupdict()

    assert parse('0.1.2') == { 'version': '0.1.2', 'base': '0.1.2', 'commits_ahead': None, 'rc': None, 'sha': None, }
    assert parse('0.1.23r1') == { 'version': '0.1.23r1', 'base': '0.1.23', 'commits_ahead': None, 'rc': 'r1', 'sha': None, }
    assert parse('0.1.23rc45') == { 'version': '0.1.23rc45', 'base': '0.1.23', 'commits_ahead': None, 'rc': 'rc45', 'sha': None, }

    v = line('git','describe','--tags','e4282e1')
    assert v == 'v0.3.7rc1-4-ge4282e1'
    assert parse(v) == { 'version': '0.3.7rc1-4-ge4282e1', 'base': '0.3.7', 'commits_ahead': '4', 'rc': 'rc1', 'sha': 'e4282e1', }


def test_pkg_version():
    assert pkg_version('python-dateutil') == '2.9.0'
