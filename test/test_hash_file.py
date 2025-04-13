from dataclasses import dataclass
from os.path import dirname, join

from utz import hash_file, HashName, parametrize

TEST_DIR = dirname(__file__)
ROOT_DIR = dirname(TEST_DIR)


@dataclass
class case:
    hash_name: HashName
    expected_hash: str
    file: str = 'src/utz/hash.py'

    @property
    def id(self):
        return f"{self.hash_name}({self.file})"


@parametrize(
    case('sha256', '26f8c940220e1d3f81a99eb46b3856cc94704336c679cd2e0d3b61ee5f47ce41'),
    case('sha384', '8d55b5142a80dc7a95298158eeaa4adf72054d681f7b51016380def5307e359b6719163678c463c55abc071b82e7da33'),
    case('sha3_256', '1310c83274fb6194eb781f5c6b49a6db0cba8968ea8f92f08c738290186090b9'),
    case('sha3_512', 'cef055919d9bc6ccf7c2e641a9b4f1ccfc3efca9409d1b96a3cf4be70257f0acc96b7e3c5619763793a87a901ff4fe8f3676e2125e4502f7aa88307e8d760e0e'),
    case('md5', '75fb9145b5f5dc52cc26be44489808c6'),
)
def test_hash_file(hash_name: HashName, expected_hash: str, file: str):
    path = join(ROOT_DIR, file)
    actual_hash = hash_file(path, hash_name=hash_name)
    assert actual_hash == expected_hash
