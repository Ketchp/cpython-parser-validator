# CLI utility for parsing python files into AST and comparing AST

Parse all `.py` files inside `.venv` directory:

`../cpython/python main.py parse --output compiled_AST/old_parser .venv`

Build python with new parser:

`../cpython/python main.py parse --output compiled_AST/new_parser .venv`

Then compare produced ASTs:

`../cpython/python main.py compare compiled_AST/old_parser compiled_AST/new_parser`
