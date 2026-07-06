"""
Offline AI Test Generator

Simulira AI generisanje pytest testova bez pozivanja eksternog API-ja.
Koristi jednostavnu analizu Python AST-a kako bi pronašao funkcije i
generisao osnovne testove.
"""

import ast
import argparse
import os


class OfflineTestGenerator:

    def generate_tests(self, source_file, output_file):

        with open(source_file, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)

        module_name = os.path.splitext(os.path.basename(source_file))[0]

        tests = [
            "import pytest",
            f"from src.{module_name} import *",
            ""
        ]

        for node in ast.walk(tree):

            if isinstance(node, ast.FunctionDef):

                if node.name.startswith("_"):
                    continue

                tests.append(f"def test_{node.name}():")

                if node.name == "add_numbers":
                    tests.append("    assert add_numbers(2, 3) == 5")
                    tests.append("")

                elif node.name == "get_user_by_username":
                    tests.append("    result = get_user_by_username('admin')")
                    tests.append("    assert 'SELECT' in result")
                    tests.append("")

                else:
                    tests.append("    # TODO: AI generated placeholder")
                    tests.append("    assert True")
                    tests.append("")

        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(tests))

        print()
        print("========================================")
        print(" Offline AI Test Generator")
        print("========================================")
        print(f"Generated: {output_file}")
        print()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    OfflineTestGenerator().generate_tests(
        args.source,
        args.output
    )
