import tomllib
from pathlib import Path


def test_inventor_extra_declares_the_verified_numeric_versions():
    manifest = tomllib.loads((Path(__file__).resolve().parents[1] / 'pyproject.toml')
                             .read_text(encoding='utf-8'))
    assert manifest['project']['optional-dependencies'].get('inventor') == [
        'networkx==3.6.1', 'numpy==2.4.3',
    ]
