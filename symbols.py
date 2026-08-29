"""Named symbol-table contract between the parser and code generators.

Until now the per-identifier entry format ({"type": ..., "array_spec": ...,
...}) existed only as a tacit agreement between parser.py (producer) and
codegen.py (consumer) -- an implicit schema with no definition point in the
data layer.  This module gives that decision a single home.

Like errors.py / tokens.py / ast_nodes.py, this file imports nothing from
the project (I = 0): pure data, no behaviour beyond field storage.
"""
from dataclasses import dataclass, field


@dataclass
class SymbolInfo:
    """One symbol-table entry.

    type       -- declared type name: "INTEGER", "REAL", "STRING", "BOOLEAN",
                  "CHAR", "DATE", "ARRAY", "CONSTANT", a class name, or "ANY"
                  for untyped parameters.
    array_spec -- for type == "ARRAY": the bounds/item-type dict built by the
                  parser (may embed AST literal nodes); None otherwise.
    item_type  -- element type name for arrays; None otherwise.
    pass_by    -- "BYVAL" or "BYREF"; only meaningful for parameters.
    """
    type: str
    array_spec: dict = None
    item_type: str = None
    pass_by: str = field(default="BYVAL")
