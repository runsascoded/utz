from utz import deterministic_gzip_open, hash_file


def test_deterministic_gzip_write():
    for i in range(2):
        with deterministic_gzip_open('a.gz', 'w') as f:
            f.write('\n'.join(map(str, range(10))))

        assert hash_file('a.gz') == "dfbe03625c539cbc2a2331d806cc48652dd3e1f52fe187ac2f3420dbfb320504"
