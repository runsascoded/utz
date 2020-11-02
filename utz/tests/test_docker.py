
from utz import docker
from utz.process import line, run
from utz.use import use


def test_docker_build():
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

