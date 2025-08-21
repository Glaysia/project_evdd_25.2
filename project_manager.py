# package import


import json
from pathlib import Path
from decimal import Decimal




class ProjectSpec:

    @staticmethod
    def load(json_path: Path = 'project.json'):
        with open(str(json_path), 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def decimals_from_step(step):
        try:
            d = Decimal(str(step)).normalize()
            exp = d.as_tuple().exponent
            return max(0, -exp)
        except Exception:
            s = str(step)
            if '.' in s:
                return len(s.split('.')[-1].rstrip('0'))
            return 0

    @staticmethod
    def inputs(json_path: Path, include_groups=None):
        data = ProjectSpec.load(json_path)
        inputs = data.get('variables', {}).get('inputs', [])
        if include_groups:
            if isinstance(include_groups, str):
                include_groups = (include_groups,)
            inputs = [it for it in inputs if it.get('group') in include_groups]
        return inputs

    @staticmethod
    def input_ranges(json_path: Path, include_groups=('geometry',)):
        inputs = ProjectSpec.inputs(json_path, include_groups=include_groups)
        ranges = {}
        for item in inputs:
            name = item.get('name')
            typ = item.get('type')
            minv = item.get('min', 0)
            maxv = item.get('max', 0)
            step = item.get('step', 1 if typ == 'int' else 0.1)
            round_digits = 0 if typ == 'int' else ProjectSpec.decimals_from_step(step)
            ranges[name] = [minv, maxv, step, round_digits]
        return ranges

    @staticmethod
    def constraint_strs(json_path: Path):
        data = ProjectSpec.load(json_path)
        return data.get('optimization', {}).get('constraint_strs', [])

    @staticmethod
    def validate(json_path: Path) -> bool:
        """
        Validate project.json consistency.

        First check: ensure the variable names listed under
        variables.feature_order (inputs/outputs) match exactly the names
        defined under variables.inputs / variables.outputs (order-agnostic).

        Returns True when valid, otherwise raises ValueError with details.
        """
        data = ProjectSpec.load(json_path)

        variables = data.get('variables', {}) or {}
        feature_order = variables.get('feature_order', {}) or {}

        # Collect declared names
        declared_inputs = {it.get('name') for it in variables.get('inputs', []) if isinstance(it, dict) and it.get('name')}
        declared_outputs = {it.get('name') for it in variables.get('outputs', []) if isinstance(it, dict) and it.get('name')}

        # Collect feature_order names
        fo_inputs = set(feature_order.get('inputs', []) or [])
        fo_outputs = set(feature_order.get('outputs', []) or [])

        errors = []

        # Inputs diff
        miss_in_fo_inputs = sorted(declared_inputs - fo_inputs)
        extra_in_fo_inputs = sorted(fo_inputs - declared_inputs)
        if miss_in_fo_inputs or extra_in_fo_inputs:
            parts = []
            if miss_in_fo_inputs:
                parts.append(f"missing_in_feature_order_inputs={miss_in_fo_inputs}")
            if extra_in_fo_inputs:
                parts.append(f"extra_in_feature_order_inputs={extra_in_fo_inputs}")
            errors.append("inputs mismatch: " + "; ".join(parts))

        # Outputs diff
        miss_in_fo_outputs = sorted(declared_outputs - fo_outputs)
        extra_in_fo_outputs = sorted(fo_outputs - declared_outputs)
        if miss_in_fo_outputs or extra_in_fo_outputs:
            parts = []
            if miss_in_fo_outputs:
                parts.append(f"missing_in_feature_order_outputs={miss_in_fo_outputs}")
            if extra_in_fo_outputs:
                parts.append(f"extra_in_feature_order_outputs={extra_in_fo_outputs}")
            errors.append("outputs mismatch: " + "; ".join(parts))

        if errors:
            raise ValueError("feature_order validation failed: " + " | ".join(errors))

        return True


if __name__ == '__main__':
    import sys

    def _run_validate():
        """Lightweight self-test for ProjectSpec.validate.

        Usage: python project_manager.py [path_to_project.json]
        """
        path_arg = sys.argv[1] if len(sys.argv) > 1 else 'project.json'
        p = Path(path_arg)
        try:
            ok = ProjectSpec.validate(p)
            print(f"VALID: {ok}")
            return 0
        except Exception as e:
            print("ERROR:", type(e).__name__, str(e))
            return 1

    raise SystemExit(_run_validate())
