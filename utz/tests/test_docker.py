from tempfile import NamedTemporaryFile

from utz import docker, line, process, run
from utz.docker.dsl import *


def test_docker_build_and_run():
    image_name = 'docker-dsl-test'
    file = docker.File()
    with file:
        FROM('bash')
        WORKDIR('/abc')
        ENTRYPOINT('pwd')
    image = file.build(image_name)
    name = f'{image_name}-{hash(image)}'
    image.run(name)
    try:
        assert line('docker','logs',name) == '/abc'
    finally:
        run('docker','container','rm',name)


def test_docker_file_contents():
    with NamedTemporaryFile(prefix='Dockerfile.') as tmpfile:
        path = tmpfile.name
        file = docker.File(path)
        with file:
            FROM('bash')
            WORKDIR('/abc')
            NOTE('Set up some env vars')
            LN()
            LABEL(**{'a.b c':'1 \n2 \n3','aaa':111})
            ENV('aaa=AAA','b=B=B',c='333')
            LABEL(r'a\\b=c\\d', bbb='BBB', **{r'e\f':'g\\h'})
            ENTRYPOINT('a', 'b c', shell=True)
            ENTRYPOINT('pwd')

        assert file.lines == [
            'FROM bash',
            'WORKDIR /abc',
            '# Set up some env vars',
            '',
            'LABEL "a.b c"="1 \\\n2 \\\n3" "aaa"="111"',
            'ENV aaa=AAA b=B=B "c"="333"',
            r'LABEL a\\b=c\\d "bbb"="BBB" "e\\f"="g\\h"',
            "ENTRYPOINT a 'b c'",
            'ENTRYPOINT ["pwd"]',
        ]

        from datetime import datetime
        now = datetime.now().strftime('%Y%m%d_%H%M%S')
        img_name = f'docker-label-env-test-{now}'
        image = file.build(img_name)
        [img] = process.json('docker','inspect',img_name)
        assert img['Config']['Labels'] == {'a.b c':'1 2 3','aaa':'111',r'a\b':r'c\d','bbb':'BBB','e\\f':'g\\h'}
        container_name = f'{img_name}-{hash(image)}'
        image.run(container_name)
        try:
            assert line('docker','logs',container_name) == '/abc'
        finally:
            run('docker','container','rm',container_name)
            run('docker','image','rm',img_name)
