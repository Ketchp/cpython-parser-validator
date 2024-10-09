#!/usr/bin/env python3

import ast
import time
import pickle
import argparse
from pathlib import Path
from itertools import batched


BATCH_SIZE = 1000
FLAGS = ast.PyCF_ONLY_AST


def ensure_is_directory(path):
    path = Path(path)
    if not path.is_dir():
        raise argparse.ArgumentTypeError("Path must be existing directory.")
    return path


def parse_cli() -> argparse.Namespace:
    cli_main = argparse.ArgumentParser(
        description="Utility for testing parser regression.",
    )
    subparsers = cli_main.add_subparsers(required=True)

    cli_parse = subparsers.add_parser(
        "parse",
        help="Parse python files to AST.",
    )

    cli_parse.add_argument(
        "input_dirs",
        nargs="+",
        help="Input directory[ies] to recursively find python files.",
        type=Path,
    )

    cli_parse.add_argument(
        "--output",
        help="Output directory to store compiled AST.\nDefault next to this script.",
        default=Path(__file__).parent / 'compiled_AST',
        type=Path,
    )

    cli_compare = subparsers.add_parser(
        "compare",
        help="Compare multiple AST.",
    )

    cli_compare.add_argument(
        "input_dirs",
        nargs=2,
        help="Compare AST in specified directories.",
        type=ensure_is_directory,
    )

    cli_parse.set_defaults(func=main_parse)
    cli_compare.set_defaults(func=main_compare)

    return cli_main.parse_args()


def main_parse(args: argparse.Namespace) -> None:
    input_dirs: list[Path] = args.input_dirs
    output_dir: Path = args.output

    inputs: list[Path] = [file.resolve() for directory in input_dirs
                                         for file in directory.rglob("*.py")]
    output_dir.mkdir(exist_ok=True, parents=True)

    time_sum = 0
    for filenames in batched(inputs, BATCH_SIZE):
        sources: dict[Path, str] = {}
        for filename in filenames:
            with open(filename, "r") as f:
                sources[filename] = f.read()

        compiled_ast: dict[Path, ast.AST] = {}
        t_start = time.time()
        for filename, source in sources.items():
            compiled_ast[filename] = compile(
                source,
                filename=filename,
                mode='exec',
                dont_inherit=True,
                flags=FLAGS,
            )
        time_sum += time.time() - t_start

        for filename, res in compiled_ast.items():
            filename = (str(filename).removesuffix('.py')
                                     .replace('/', '.') + '.bin')
            with open(output_dir / filename, "wb") as f:
                pickle.dump(res, f)

    with open(output_dir / "time.txt", "a") as f:
        f.write(f'{len(inputs)} took: {time_sum}s\n')


def main_compare(args: argparse.Namespace) -> None:
    dir0: Path
    dir1: Path
    dir0, dir1 = args.input_dirs

    warn = False
    error = False

    dir1_files = {file.name for file in dir1.iterdir()} - {'time.txt'}
    for filename in dir0.iterdir():
        filename = filename.name
        if filename == 'time.txt':
            continue
        try:
            dir1_files.remove(filename)
        except KeyError:
            print(f"Warning: file {filename} exists in {dir0}, but not in {dir1}.")
            warn = True
            continue
        with (open(dir0 / filename, "rb") as f0,
              open(dir1 / filename, "rb") as f1):
            if f0.read() != f1.read():
                print(f"Error: file {filename} does not match.")
                error = True

    if dir1_files:
        print(f"Warning: files {dir1_files} exists in {dir1}, but not in {dir0}.")
        warn = True

    if error:
        print("TEST FAILED")
    elif warn:
        print("TEST PASSED WITH WARNINGS")
    else:
        print("TEST PASSED")


def main():
    args = parse_cli()
    return args.func(args)


if __name__ == '__main__':
    exit(main())
