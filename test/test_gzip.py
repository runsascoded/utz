from utz import deterministic_gzip_open, hash_file


def test_deterministic_gzip_write(tmp_path):
    path = tmp_path / 'a.gz'
    for i in range(2):
        with deterministic_gzip_open(path, 'w') as f:
            f.write('\n'.join(map(str, range(10))))

        assert hash_file(path) == "dfbe03625c539cbc2a2331d806cc48652dd3e1f52fe187ac2f3420dbfb320504"
