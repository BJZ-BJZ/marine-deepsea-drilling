"""Synthetic examples for a statistical screening interface; no new rig experiment."""
import json
from envelope import select_candidate

examples=[(900.,20.,100.),(1250.,20.,100.),(900.,80.,100.),(900.,20.,300.)]
selected=[select_candidate(*values) for values in examples]
assert selected==[True,False,False,False]
print(json.dumps(dict(status='PASS',input='Synthetic kPa-channel examples',selected=selected,
    scope='Illustrative statistical screening; not physical torque calibration or certified safety.')))
