"""Statistical command screening from archived P26-194 thresholds.

These limits are local data-derived heuristics, not certified equipment limits.
"""
import math

def select_candidate(channel_kpa, positive_increment_kpa_per_step, absolute_residual_kpa,
                     channel_limit=1212.126, increment_limit=67.29, residual_limit=259.834):
    values=(channel_kpa,positive_increment_kpa_per_step,absolute_residual_kpa)
    if not all(math.isfinite(x) for x in values) or absolute_residual_kpa<0:
        raise ValueError('Expected finite pressure-channel quantities and nonnegative absolute residual')
    return channel_kpa<channel_limit and positive_increment_kpa_per_step<increment_limit and absolute_residual_kpa<residual_limit
