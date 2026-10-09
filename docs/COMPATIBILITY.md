# Explicit compiler, codec, and semantic boundaries

Use `from pyecoreocl import dummy_compiler` as the reference API. It returns a
Python expression; parse/compile it with Python's AST/compiler and supply the
trusted application context needed by that expression. Example:

```python
import ast
from pyecoreocl import dummy_compiler

source = dummy_compiler("let x = 4 in let y = x + 1 in x + y")
code = compile(ast.parse(source, mode="eval"), "<trusted-ocl>", "eval")
assert eval(code) == 9
```

Depending on the expression, generated code also uses `pyecoreocl.runtime` as
`ocl`, `itertools`, `collections`, `typing`, and application names such as `self`.
The codec supplies the runtime imports; the explicit API leaves these bindings to
the caller. Neither path is a sandbox. Only trusted fixtures are executed here.

Syntax errors from ANTLR and trailing input raise `SyntaxError` with filename
`<ocl>`, one-based line and offset, and source text. Invalid compiler modes raise
`ValueError`. Syntax diagnostics do not constitute semantic/type checking; the
historical constant-evaluation actions may still raise Python exceptions while
parsing valid syntax (for example `1 / 0`).

## Scope and known historical limits

Nested `let`, lexical shadowing, outer-variable initializers, generator/lambda
capture, ordinary Python objects and EObject navigation are tested in normal and
strict mode. Lambda generation is preserved. Dependent initializers within one
multi-variable `let` remain unsupported: `let x = 1, y = x + 1 in y` evaluates the
initializer of `y` outside the lambda binding `x`. Use nested `let` for that case.

The compiler remains a Python-oriented partial translation, not full OCL:

- Both `null` and `invalid` compile to Python `None`; four-valued OCL propagation
  is not implemented. Operations on them may raise ordinary Python exceptions.
- `at` and string indexing use zero-based Python indices; range literals use an
  exclusive upper bound. Existing behavior is retained.
- OrderedSet literals are lists and retain duplicates. Set literals use Python
  sets. Some operations return lazy generators rather than OCL collection types.
- Normal mode supports implicit collect for attribute navigation; strict mode
  uses direct Python attributes. Implicit iterator forms such as the unadapted
  UML Class.getSuperClasses derivation remain unsupported.
- No general static semantic analysis, type validation, or execution of arbitrary
  Ecore annotation text is claimed. Untested collection operations are not
  inferred to work from grammar/rule presence.

## Codec qualification

The existing dependency `magic_codec` is retained so historical default installs
continue to decode `# coding: magic_ocl`, `.normal`, and `.strict` files. The
explicit compiler itself imports no magic_codec. Standalone qualification also
runs the compiler without site initialization or magic_codec on the import path.

Tests separate local `magic_ocl.preprocess` from the unchanged external codec:
whole-byte decoding, consumed byte counts, incremental decoding across a split
Unicode character, and imports of trusted encoded files. Standard Python string
literals, comments, `!=`, and f-string/template-string conversions are preserved.
OCL delimiters inside interpolated strings are not supported; write the OCL
expression separately. Template strings are preserved, not backported below 3.14.
An unmatched OCL delimiter raises a located `SyntaxError` rather than silently
truncating the module. No magic_codec fork is introduced.

## Parser and distributions

The checked-in parser/lexer/visitor/listener headers and parser/lexer version
checks identify ANTLR **4.13.2**. The runtime remains pinned to 4.13.2. Generated
files and grammar are unchanged; no generator executable is downloaded or large
regeneration performed. The grammar and token/interp files are retained in the
distributions for traceability, along with the original license. The generator
version is checked from these existing artifacts, not by claiming a new generation.

## UML candidates, not integration

`tests/data/uml_candidates.json` records the original model SHA-256, namespace,
XPath, context, result type, and extracted expression body for three candidates.
Only the `result =` documentary wrapper is removed; no automatic annotation
rewriting takes place.

| Source | Explicit context | Test/result | Status |
| --- | --- | --- | --- |
| Property.isComposite | PyEcore enum AggregationKind and explicitly bound aggregation from an EObject Property | none → False; composite → True; shared → False after mutation | supported expression, explicit bindings required |
| NamedElement.separator | none; String result | `::` in both modes | supported helper for qualified names |
| Class.getSuperClasses / superClass | UML Class; Set(Class) | compiler AttributeError on implicit iterator form | historical unsupported form, tested as a limit |

These fixtures test compiler candidates, not the complete UML operations or the
shipped PyUML2 mixins. Source model release/license uncertainty recorded by T10
remains unresolved; no claim of upstream model provenance is added here. No code
is installed into PyUML2 and no profiles/SysML/legacy branch is merged.
