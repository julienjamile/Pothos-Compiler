"""
compiler/__init__.py  –  Pothos compiler package (lexical phase + pipeline).

    from compiler import compile_source
    result = compile_source(source, options)
"""
from .pipeline import compile_source

__all__ = ["compile_source"]
