from utz.proc import sh


class Image:
    def __init__(self, url, file=None):
        self.url = url
        self.file = file

    def run(self, name=None, rm=False,):
        sh(
            'docker','run',
            ['--name',name] if name else None,
            '--rm' if rm else None,
            self.url,
        )
