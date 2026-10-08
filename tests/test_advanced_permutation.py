"""Input-order invariance checked across all ten advanced calculations."""
from __future__ import annotations

import importlib
import json
import random
from copy import deepcopy
from pathlib import Path

import pytest
from test_advanced_analytical_oracles import NAMES, make_rows

EXAMPLES = Path(__file__).resolve().parents[1] / 'examples' / 'advanced'


@pytest.mark.parametrize('name', NAMES)
@pytest.mark.parametrize('seed', [5, 23, 47, 101, 251, 997])
def test_permuting_records_and_memberships_preserves_the_complete_result(name, seed):
    module = importlib.import_module(f'patent_analysis.analyses.{name}')
    spec = json.loads(
        (EXAMPLES / f'{module.ANALYSIS_ID[:-3]}.json').read_text(encoding='utf-8')
    )
    rows = make_rows(seed)
    expected = module.compute(rows, spec['parameters'])
    shuffled = deepcopy(rows)
    rng = random.Random(seed + 10000)
    rng.shuffle(shuffled)
    for row in shuffled:
        for role in tuple(row):
            tokens = list(row[role])
            rng.shuffle(tokens)
            row[role] = tuple(tokens)
    assert module.compute(shuffled, spec['parameters']) == expected
