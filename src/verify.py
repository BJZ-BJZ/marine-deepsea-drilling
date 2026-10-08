"""Replay archived predictions, validation assignments and operational envelope.

CSV serialization rounds XGBoost predictions: allow 1e-5 absolute metric error.
No model is fitted in this verifier.
"""

if not __debug__:
    raise RuntimeError('Verification requires assertions: do not use -O, -OO or PYTHONOPTIMIZE')
from collections import Counter
from pathlib import Path
import csv
import hashlib
import json
import numpy as np
from envelope import select_candidate

DATA=Path(__file__).resolve().parents[1]/'data'
def read(name):
    with (DATA/name).open(encoding='utf-8') as stream:return list(csv.DictReader(stream))
facts=json.loads((DATA/'paper_facts.json').read_text(encoding='utf-8'))
raw=DATA/'Well_58-32_processed_pason_log.csv'
assert hashlib.sha256(raw.read_bytes()).hexdigest()==facts['source_sha256']
assert len(read(raw.name))==facts['samples']['raw']==7311
predictions=read('predictions_all_splits_revised.csv')
metrics=read('metrics_by_model_revised.csv')
assignments=read('split_assignments.csv')
by_split={}
for row in assignments:
    mapping=by_split.setdefault(row['split'],{})
    index=int(row['source_index']);assert index not in mapping
    mapping[index]=row['assignment']
assert len(by_split)==3
counts={}
for split,mapping in by_split.items():
    assert len(mapping)==6584 and set(mapping)==set(range(6584))
    counts[split]=dict(Counter(mapping.values()))
    test={i for i,label in mapping.items() if label=='test'}
    observed=[int(r['source_index']) for r in predictions if r['split']==split]
    assert len(observed)==len(set(observed)) and set(observed)==test
    if split=='depth_holdout':assert test==set(range(4608,6584))
    if split=='contiguous_block_holdout':assert max(test)-min(test)+1==len(test)==1317
columns={'MSE_Ridge_baseline':'mse_ridge_baseline','RandomForest_direct':'random_forest_direct',
    'XGBoost_direct':'xgboost_direct','XGBoost_direct_without_torque_history':'xgboost_direct_without_torque_history',
    'PGML_XGBoost_residual':'residual_xgboost'}
errors=[]
for metric in metrics:
    rows=[r for r in predictions if r['split']==metric['split']]
    y=np.array([float(r['measured_torque_kpa']) for r in rows])
    prediction=np.array([float(r[columns[metric['model']]]) for r in rows])
    residual=prediction-y
    actual=[1-np.sum(residual**2)/np.sum((y-y.mean())**2),np.sqrt(np.mean(residual**2)),
            np.mean(np.abs(residual)),np.mean(np.abs(residual/y))*100]
    expected=[float(metric[name]) for name in ['R2','RMSE_kPa','MAE_kPa','MAPE_pct']]
    errors.extend(np.abs(np.array(actual)-expected))
    assert np.allclose(actual,expected,rtol=0,atol=1e-5)
assert len(metrics)==15
grid=read('operational_envelope_grid_revised.csv')
accepted=0
for row in grid:
    selected=select_candidate(float(row['predicted_torque_kpa']),float(row['predicted_growth_kpa_per_depth_step']),
                              float(row['absolute_residual_correction_kpa']))
    assert selected==(row['safe']=='True')
    accepted+=selected
assert len(grid)==2025 and accepted==1178
print(json.dumps(dict(status='PASS',source_hash_and_raw_rows_verified=True,modeling_rows=6584,
    validation_counts=counts,model_split_metrics=15,scalar_metrics=60,max_absolute_metric_discrepancy=float(max(errors)),
    envelope_candidates=2025,envelope_accepted=accepted,acceptance_fraction=accepted/2025,
    scope='Numerical replay and assignment/threshold audit; no new training, SHAP recomputation or deepsea field validation.')))
