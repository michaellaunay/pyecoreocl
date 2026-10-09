"""Qualify the unchanged external magic_codec independently of dummy_compiler."""
import codecs
import importlib.util

import pytest
import magic_codec.register  # explicit alternative to the installed .pth hook


@pytest.mark.parametrize('encoding', ['magic_ocl', 'magic_ocl.normal', 'magic_ocl.strict'])
def test_decoder_and_incremental_unicode(encoding):
    source = "value = !'Été'!\n".encode('utf-8')
    codec = codecs.lookup(encoding)
    text, consumed = codec.decode(source)
    assert consumed == len(source)
    namespace = {}
    exec(compile(text, '<codec-decoder>', 'exec'), namespace)
    assert namespace['value'] == 'Été'
    decoder = codec.incrementaldecoder()
    split = source.index(b'\xc3') + 1
    assert decoder.decode(source[:split]) == ''
    text = decoder.decode(source[split:], final=True)
    namespace = {}
    exec(compile(text, '<codec-incremental>', 'exec'), namespace)
    assert namespace['value'] == 'Été'


@pytest.mark.parametrize('mode', ['normal', 'strict'])
def test_encoded_module_import(tmp_path, mode):
    path = tmp_path / ('trusted_' + mode + '.py')
    path.write_bytes((f'# coding: magic_ocl.{mode}\nresult = !let x = 4 in x + 1!\n').encode())
    spec = importlib.util.spec_from_file_location('trusted_' + mode, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.result == 5
