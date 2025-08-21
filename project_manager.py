# package import


import json
from pathlib import Path
from decimal import Decimal




class ProjectSpec:

    @staticmethod
    def load(json_path: Path):
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
            if typ == 'bool':
                ranges[name] = [0, 1, 1, 0]
                continue
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