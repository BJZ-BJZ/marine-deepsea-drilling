"""Generate research figures from real project data. One figures/ dir per repo."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update({
    'figure.dpi': 160, 'savefig.dpi': 160,
    'font.size': 10, 'axes.titlesize': 12, 'axes.labelsize': 10,
    'xtick.labelsize': 9, 'ytick.labelsize': 9, 'legend.fontsize': 9,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.alpha': 0.3,
})
PALETTE = ['#1f6f9f', '#d96c2c', '#3a9e6e', '#8e5aa8', '#c0a02e', '#4aa3c7', '#e07b7b', '#6e7f80']

REPOS = Path(__file__).resolve().parents[1]
rng = np.random.default_rng(7)


def savefig(fig, path):
    fig.tight_layout()
    fig.savefig(path, bbox_inches='tight')
    plt.close(fig)
    print('wrote', path)


def drilling_figs(d):
    m = pd.read_csv(d / 'data/metrics_by_model_revised.csv')
    # fig1: RMSE by model x split
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    splits = m['split'].unique()
    models = m['model'].unique()
    x = np.arange(len(splits)); w = 0.8 / len(models)
    for i, md in enumerate(models):
        vals = [m[(m['split'] == s) & (m['model'] == md)]['RMSE_kPa'].values[0] for s in splits]
        ax.bar(x + (i - len(models) / 2 + 0.5) * w, vals, w, color=PALETTE[i % len(PALETTE)],
               label=md.replace('_', ' '), edgecolor='k', lw=0.4)
    ax.set_xticks(x); ax.set_xticklabels([s.replace('_', ' ') for s in splits], rotation=10, ha='right')
    ax.set_ylabel('RMSE (kPa)')
    ax.set_title('Torque prediction RMSE by model and split')
    ax.legend(fontsize=8, ncol=2)
    savefig(fig, d / 'figures/fig1_model_rmse_by_split.png')
    # fig2: parity plot (sampled)
    p = pd.read_csv(d / 'data/predictions_all_splits_revised.csv',
                    usecols=['measured_torque_kpa', 'xgboost_direct'])
    p = p.sample(min(4000, len(p)), random_state=7)
    fig, ax = plt.subplots(figsize=(5.4, 5.2))
    ax.scatter(p['measured_torque_kpa'], p['xgboost_direct'], s=6, alpha=0.25, color=PALETTE[0])
    lo = min(p.min().min(), 0); hi = p.max().max()
    ax.plot([lo, hi], [lo, hi], 'k--', lw=1)
    r2 = m[(m['split'] == 'random_within_well') & (m['model'] == 'XGBoost_direct')]['R2'].values[0]
    ax.set_xlabel('Measured torque (kPa)'); ax.set_ylabel('XGBoost predicted torque (kPa)')
    ax.set_title(f'Parity plot — XGBoost direct (R² = {r2:.3f}, random split)')
    ax.set_aspect('equal', adjustable='box')
    savefig(fig, d / 'figures/fig2_parity_xgboost.png')
    # fig3: WOB-RPM envelope heatmap
    g = pd.read_csv(d / 'data/operational_envelope_grid_revised.csv',
                    usecols=['wob_kg', 'rpm', 'predicted_torque_kpa'])
    g['wob_bin'] = pd.cut(g['wob_kg'], 24); g['rpm_bin'] = pd.cut(g['rpm'], 24)
    piv = g.pivot_table(values='predicted_torque_kpa', index='wob_bin', columns='rpm_bin',
                        aggfunc='mean', observed=True)
    wob_centers = [iv.mid for iv in piv.index]
    rpm_centers = [iv.mid for iv in piv.columns]
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    im = ax.imshow(piv.values, origin='lower', aspect='auto', cmap='YlOrRd')
    tick = np.linspace(0, 23, 6).astype(int)
    ax.set_xticks(tick); ax.set_xticklabels([f'{rpm_centers[i]:.0f}' for i in tick])
    ax.set_yticks(tick); ax.set_yticklabels([f'{wob_centers[i]:.0f}' for i in tick])
    ax.set_xlabel('RPM'); ax.set_ylabel('WOB (kg)')
    ax.set_title('Predicted torque envelope over WOB–RPM')
    fig.colorbar(im, ax=ax, label='Predicted torque (kPa)')
    savefig(fig, d / 'figures/fig3_envelope_heatmap.png')
    # fig4: SHAP importance
    s = pd.read_csv(d / 'data/shap_residual_summary_heldout.csv').sort_values('mean_abs_shap')
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.barh(s['feature'], s['mean_abs_shap'], color=PALETTE[2], edgecolor='k', lw=0.5)
    ax.set_xlabel('Mean |SHAP| (kPa)')
    ax.set_title('Residual XGBoost feature importance (held-out)')
    savefig(fig, d / 'figures/fig4_shap_importance.png')



if __name__ == '__main__':
    d = REPOS
    (d / 'figures').mkdir(exist_ok=True)
    drilling_figs(d)
    print('done')
