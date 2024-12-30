from os.path import dirname, join

TEST = dirname(__file__)
ROOT = dirname(TEST)
DATA = join(TEST, 'data')
GSMO = join(DATA, 'gsmo')
HAILSTONE = join(GSMO, 'example/hailstone')
