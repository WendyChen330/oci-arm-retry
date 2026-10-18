from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def literal_assignments(path: Path) -> dict[str, object]:
    tree = ast.parse(path.read_text())
    values: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        try:
            values[target.id] = ast.literal_eval(node.value)
        except (ValueError, TypeError):
            continue
    return values


def test_arm_shape_configuration() -> None:
    values = literal_assignments(ROOT / "oci_retry.py")
    assert values["ARM_SHAPE"] == "VM.Standard.A1.Flex"
    assert values["UBUNTU_VERSION"] == "24.04"
    assert values["ARM_OCPUS"] == 1
    assert values["ARM_MEMORY_IN_GBS"] == 6


def test_workflow_relay_uses_builtin_token_and_current_ref() -> None:
    for name in ("oci_retry.yml", "oci_retry_micro.yml"):
        workflow = (ROOT / ".github" / "workflows" / name).read_text()
        assert "actions: write" in workflow
        assert "GH_TOKEN: ${{ github.token }}" in workflow
        assert "github.ref_name" in workflow
        assert "GH_PAT" not in workflow
        assert 'ref":"main' not in workflow


if __name__ == "__main__":
    test_arm_shape_configuration()
    test_workflow_relay_uses_builtin_token_and_current_ref()
    print("configuration tests passed")
