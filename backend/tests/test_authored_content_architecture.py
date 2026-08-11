import ast
from pathlib import Path


def test_authored_content_has_no_simulation_import_boundary_violation():
    root = Path("app/authored_content")
    forbidden_names = {"SimulationState", "process_week"}
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                modules = (
                    [alias.name for alias in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module or ""]
                )
                assert all(not module.startswith("app.simulation") for module in modules), path
                assert all(not module.endswith("randomness") for module in modules), path
            if isinstance(node, ast.Name):
                assert node.id not in forbidden_names, path
