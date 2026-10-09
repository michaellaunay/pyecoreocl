"""Explicit compilation of trusted fixtures, independent from the source codec."""
import ast
import collections
import itertools
from types import SimpleNamespace
import typing

import pytest
from pyecoreocl import dummy_compiler
import pyecoreocl.runtime as ocl


def evaluate(expression, mode='normal', **context):
    generated = dummy_compiler(expression, mode=mode)
    tree = ast.parse(generated, mode='eval')
    code = compile(tree, '<generated-ocl>', 'eval')
    namespace = dict(ocl=ocl, itertools=itertools, collections=collections, typing=typing)
    namespace.update(context)
    return eval(code, namespace), tree


@pytest.mark.parametrize('mode', ['normal', 'strict'])
@pytest.mark.parametrize('expression,expected', [
    ('let x = 4 in let y = x - 1 in x + y', 7),
    ('let x = 4 in (let x = 2 in x) + x', 6),
    ('let x = external in let y = x + 1 in y + x', 11),
    ('let x = 10 in Sequence{1,2}->collect(e | e + x)->asSequence()', [11, 12]),
    ('let x = 1 in let values = Sequence{1,2}->collect(e | e + x) in let x = 10 in values->asSequence()', [2, 3]),
    ('if flag then 3 else 4 endif', 3),
    ('Sequence{3,1,2}->select(e | e > 1)->asSequence()', [3, 2]),
    ('Set{1,1,2}->size()', 2),
    ('null', None),
    ('invalid', None),
])
def test_explicit_ast_scope_and_collections(mode, expression, expected):
    result, tree = evaluate(expression, mode, external=5, flag=True)
    assert isinstance(tree, ast.Expression)
    assert result == expected


@pytest.mark.parametrize('mode', ['normal', 'strict'])
def test_deferred_lambda_capture(mode):
    result, tree = evaluate('let x = external in values->collect(e | e + x)',
                            mode, external=5, values=[1, 2])
    assert isinstance(tree, ast.Expression)
    assert list(result) == [6, 7]


@pytest.mark.parametrize('mode', ['normal', 'strict'])
def test_python_and_eobject_navigation(mode):
    from pyecore.ecore import EClass, EAttribute, EString
    person = EClass('Person')
    person.eStructuralFeatures.append(EAttribute('name', EString))
    for obj in (SimpleNamespace(name='Été'), person(name='Été')):
        result, _ = evaluate("self.name = 'Été'", mode, self=obj)
        assert result is True


@pytest.mark.parametrize('expression', ['1 +', '1 2', '@', 'true garbage', 'let x = in x'])
def test_invalid_input_is_a_located_diagnostic(expression):
    with pytest.raises(SyntaxError) as error:
        dummy_compiler(expression)
    assert error.value.lineno == 1
    assert error.value.offset >= 1
    assert error.value.filename == '<ocl>'


def test_invalid_mode_is_reported():
    with pytest.raises(ValueError, match='mode'):
        dummy_compiler('1', mode='typo')


def test_prior_semantic_limits_are_explicit():
    # Historical Python-oriented semantics, not complete OCL semantics.
    assert evaluate('null')[0] is evaluate('invalid')[0] is None
    assert evaluate('Sequence{1,2}->at(0)')[0] == 1
    assert evaluate('Sequence{1..3}')[0] == [1, 2]
    assert evaluate('OrderedSet{1,1,2}')[0] == [1, 1, 2]
    with pytest.raises(TypeError):
        evaluate('null + 1')
    with pytest.raises(ZeroDivisionError):
        dummy_compiler('1 / 0')


def test_let_ast_keeps_nested_lambda_bindings():
    tree = ast.parse(dummy_compiler('let x = 4 in let y = x + 1 in x + y'), mode='eval')
    assert isinstance(tree.body, ast.Call)
    outer = tree.body.func
    assert isinstance(outer, ast.Lambda)
    assert [arg.arg for arg in outer.args.args] == ['x']
    inner = outer.body.func
    assert isinstance(inner, ast.Lambda)
    assert [arg.arg for arg in inner.args.args] == ['y']
    assert isinstance(outer.body.args[0], ast.BinOp)


def test_located_error_then_success(capsys):
    with pytest.raises(SyntaxError) as error:
        dummy_compiler('\n1 +')
    assert error.value.lineno == 2
    assert dummy_compiler('2 + 3') == '5'
    output = capsys.readouterr()
    assert output.out == output.err == ''


def test_multiple_let_initializer_dependency_is_a_historical_limit():
    # Multiple parameters are initialized outside the generated lambda body.
    with pytest.raises(NameError):
        evaluate('let x = 1, y = x + 1 in y')
