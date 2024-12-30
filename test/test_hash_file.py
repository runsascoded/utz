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
    case('sha256', '716375ae080e9540daa3e268082d4b1f846e3f9d0c6e8321946a94b8daca5edc'),
    case('sha384', '831fbf1e14b48840b2061d18cf669f256b62db331c8f1303ec371eedc0675e099cffb81b7f1f9c8cff11098328241895'),
    case('sha3_256', '9c7c214c492f78e7556778abe0b5e8cab32b6ae15d845a96104afe1612998f8e'),
    case('sha3_512', '13cc2e058324082afe7c33d7f7f3897a03ea3de8c37640dffeaf621509fe48ceaa995380c543c7d342b877d4095bea89ba455f8a7713a0d63d6b2a876a5dbe82'),
    case('md5', '22d98a8137d748354bdfa9805044c335'),
)
def test_hash_file(hash_name: HashName, expected_hash: str, file: str):
    path = join(ROOT_DIR, file)
    actual_hash = hash_file(path, hash_name=hash_name)
    assert actual_hash == expected_hash
