
import os

from utz import docker, process
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
        LABEL(**{'a.b c':'1 \n2 \n3','aaa':111})
        ENV('aaa=AAA','b=B=B',c='333')
        LABEL(r'a\\b=c\\d', bbb='BBB', **{r'e\f':'g\\h'})
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
            'LABEL "a.b c"="1 \\','2 \\','3" "aaa"="111"',
            'ENV aaa=AAA b=B=B "c"="333"',
            r'LABEL a\\b=c\\d "bbb"="BBB" "e\\f"="g\\h"',
            'ENTRYPOINT pwd',
        ]

    from datetime import datetime
    now = datetime.now().strftime('%Y%m%d_%H%M%S')
    img_name = f'docker-label-env-test-{now}'
    image = file.build(img_name, closed_ok=True)
    [img] = process.json('docker','inspect',img_name)
    assert img['Config']['Labels'] == {'a.b c':'1 2 3','aaa':'111',r'a\b':r'c\d','bbb':'BBB','e\\f':'g\\h'}
    container_name = f'{img_name}-{hash(image)}'
    image.run(container_name)
    try:
        assert line('docker','logs',container_name) == '/abc'
    finally:
        run('docker','container','rm',container_name)
        run('docker','image','rm',img_name)
