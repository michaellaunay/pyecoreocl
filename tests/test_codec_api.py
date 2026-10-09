"""Local source transformation, separately from magic_codec registration."""
import pytest
from magic_ocl import preprocess


def test_plain_python_fstring_conversion_is_preserved():
    source = 'name = "Été"\nresult = f"{name!r}"\n'
    namespace = {}
    exec(compile(preprocess(source), '<codec-fixture>', 'exec'), namespace)
    assert namespace['result'] == repr('Été')


def test_strings_comments_and_python_inequality():
    source = '# !this is a comment!\ntext = "!literal!"\nx = 2 != 3\nresult = !let n = 2 in n + 1!\n'
    namespace = {}
    exec(compile(preprocess(source), '<codec-fixture>', 'exec'), namespace)
    assert namespace['text'] == '!literal!'
    assert namespace['x'] is True
    assert namespace['result'] == 3


def test_unclosed_ocl_is_a_located_diagnostic():
    with pytest.raises(SyntaxError) as error:
        preprocess('result = !1 + 2\n')
    assert error.value.lineno == 1
    assert error.value.offset == 10


def test_template_string_conversion_is_preserved():
    import sys
    source = 'name = "Été"\nresult = t"{name!r}"\n'
    generated = preprocess(source)
    assert 'name!r' in generated
    if sys.version_info < (3, 14):
        # The codec preserves syntax; it does not backport template strings.
        with pytest.raises(SyntaxError):
            compile(generated, '<template-fixture>', 'exec')
    else:
        namespace = {}
        exec(compile(generated, '<template-fixture>', 'exec'), namespace)
        assert namespace['result'].interpolations[0].value == 'Été'
        assert namespace['result'].interpolations[0].conversion == 'r'
