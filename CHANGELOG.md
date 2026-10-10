# Changelog

## Unreleased — Python 3.14 migration (release decision pending)

- CPython >=3.12 metadata; qualified 3.12/3.13/3.14 standard with GIL on Linux x86_64 only.
- Build backend setuptools >=83.0.0 and test extra pytest >=9.0.3. Project/module names, nsURI, licenses and author credits are retained.
- Kept the explicit compiler API and magic_ocl codec, with localized syntax/trailing-input diagnostics.
- Codec preserves Python interpolation; nested let, lexical capture and installed parser/grammar resources are qualified.
- ANTLR generated sources and runtime remain at 4.13.2; no bulk parser/UML regeneration is integrated.

Prefer the explicit dummy_compiler API for trusted expressions. Review docs/COMPATIBILITY.md: null and invalid both map to None, indexing is zero-based, ranges exclude the upper bound, dependent initializers in a single multi-variable let remain unsupported. Use nested let. Generated/evaluated Python is not a sandbox or full OCL implementation.

