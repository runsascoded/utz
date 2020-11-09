
import os

from utz import docker
from utz.process import line, run
from utz.use import use


def test_docker_build_and_run():
    file = docker.File()
    with use(file):
        FROM('bash')
        WORKDIR('/abc')
        ENTRYPOINT('pwd')
    image = file.build('docker-dsl-test')
    name = f'docker-dsl-test-{hash(image)}'
    image.run(name)
    try:
        assert line('docker','logs',name) == '/abc'
    finally:
        run('docker','container','rm',name)


def test_docker_file_contents():
    file = docker.File()
    with use(file):
        FROM('bash')
        WORKDIR('/abc')
        NOTE('Set up some env vars')
        LN()
        ENV('aaa=AAA','b=B=B',c='333')
        ENTRYPOINT('pwd')
    file.close()
    path = file.path
    with open(path,'r') as f:
        lines = [ line.strip() for line in f.readlines() ]
        assert lines == [
            'FROM bash',
            'WORKDIR /abc',
            '# Set up some env vars',
            '',
            'ENV aaa=AAA',
            'ENV b=B=B',
            'ENV c=333',
            'ENTRYPOINT pwd',
        ]
    os.remove(path)
