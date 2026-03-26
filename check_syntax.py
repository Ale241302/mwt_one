import os
import ast

def check_syntax(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        source = f.read()
                        ast.parse(source)
                except SyntaxError as e:
                    print(f"Syntax error in {path}: {e}")
                except UnicodeDecodeError:
                    # Try with other encoding if needed
                    try:
                        with open(path, "r", encoding="latin-1") as f:
                            ast.parse(f.read())
                    except Exception as e:
                        print(f"Error reading {path}: {e}")
                except Exception as e:
                    pass

check_syntax("backend")
