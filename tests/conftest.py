"""Keep every imported ecosystem/runtime module within its qualified root."""
from pathlib import Path
import sys


def pytest_sessionstart(session):
    import pyecore, pyecoreocl, magic_ocl, magic_codec, antlr4
    session._runtime_roots = {
        module.__name__: Path(module.__file__).resolve().parent
        for module in (pyecore, pyecoreocl, magic_ocl, magic_codec, antlr4)
    }


def pytest_sessionfinish(session, exitstatus):
    for name, module in list(sys.modules.items()):
        root = session._runtime_roots.get(name.split('.')[0])
        if root is not None and getattr(module, '__file__', None):
            assert Path(module.__file__).resolve().is_relative_to(root), (name, module.__file__)
