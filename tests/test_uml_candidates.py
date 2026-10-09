"""Traceable expression candidates, without generating/installing UML code."""
import ast
import json
from pathlib import Path

import pytest
from pyecore.ecore import EClass, EEnum, EAttribute
from pyecoreocl import dummy_compiler
import pyecoreocl.runtime as ocl

CANDIDATES = json.loads((Path(__file__).with_name('data') / 'uml_candidates.json').read_text())


@pytest.mark.parametrize('mode', ['normal', 'strict'])
def test_property_composite_after_mutation(mode):
    candidate = CANDIDATES[0]
    aggregation = EEnum('AggregationKind', literals=['none', 'shared', 'composite'])
    property_type = EClass('Property')
    property_type.eStructuralFeatures.append(EAttribute('aggregation', aggregation))
    obj = property_type()
    code = compile(ast.parse(dummy_compiler(candidate['expression'], mode), mode='eval'),
                   '<uml-isComposite-candidate>', 'eval')
    for literal, expected in [(aggregation.none, False), (aggregation.composite, True), (aggregation.shared, False)]:
        obj.aggregation = literal
        # Explicit binding of UML's implicit self property; no model rewriting.
        assert eval(code, dict(ocl=ocl, aggregation=obj.aggregation, AggregationKind=aggregation)) is expected


@pytest.mark.parametrize('mode', ['normal', 'strict'])
def test_separator_candidate(mode):
    assert eval(compile(dummy_compiler(CANDIDATES[1]['expression'], mode),
                        '<uml-separator-candidate>', 'eval')) == '::'


def test_superclass_implicit_iterator_remains_unsupported():
    with pytest.raises(AttributeError, match='accept'):
        dummy_compiler(CANDIDATES[2]['expression'])
