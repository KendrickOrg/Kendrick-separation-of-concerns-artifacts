#!/usr/bin/env python3
"""
Compares the AlgebraicPetri trajectory of a model (algebraicpetri models/model3.jl, or model4/model4.jl)
with the Kendrick one, compartment by compartment, with the measure of compare.py (largest deviation over
the integer days, relative to the peak of the reference series; here the reference is Kendrick), then with
the Octave one of the MATLAB model, the reference being Octave.

    python3 tools/compare/compare_algebraicpetri.py [3|4]       (from the root of the repository; 3 by default)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare as C

ROOT = C.ROOT
model = sys.argv[1] if len(sys.argv) > 1 else "3"
t_k, k = C.read(os.path.join(ROOT, "generated", "kendrick-trajectories", f"Model{model}.csv"))
t_j, j = C.read(os.path.join(ROOT, "generated", "algebraicpetri-trajectories", f"Model{model}.csv"))
assert len(t_k) == len(t_j) and all(abs(a - b) < 1e-9 for a, b in zip(t_k, t_j)), "time grids differ"
n = len(t_k)
missing = [c for c in k if c not in j]
extra = [c for c in j if c not in k]
assert not missing and not extra, (missing[:5], extra[:5])
per = {}
for c in k:
    rel, dev, at, peak = C.deviation(j[c], k[c])
    per[c] = (rel, dev, peak, t_k[at])
worst = max((c for c in per if per[c][0] is not None), key=lambda c: per[c][0])
print(f"Model {model}: {len(k)} compartments compared; worst {worst}: rel {per[worst][0]:.2e}, |diff| {per[worst][1]:.3g}, "
      f"peak {per[worst][2]:.5g}, day {per[worst][3]:.0f}")
ak, aj = C.aggregate(k, n), C.aggregate(j, n)
agg = {key: C.deviation(aj[key], ak[key]) for key in ak}
wa = max(agg, key=lambda key: agg[key][0])
print(f"aggregated series: worst {wa}: rel {agg[wa][0]:.2e}")
tot_k = [sum(k[c][i] for c in k) for i in range(n)]
tot_j = [sum(j[c][i] for c in j) for i in range(n)]
print(f"population {tot_k[0]:.6g}: drift {max(abs(v - tot_j[0]) for v in tot_j):.3g} (AlgebraicPetri), "
      f"{max(abs(v - tot_k[0]) for v in tot_k):.3g} (Kendrick)")

# The same measure against the Octave trajectory of the hand-written MATLAB model, the reference being Octave.
# The two formulations are written independently of Kendrick; compartments that MATLAB does not have are reported
# by their largest value.
mpath = os.path.join(ROOT, "generated", "matlab-trajectories", f"M{model}.csv")
if os.path.exists(mpath):
    t_m, m = C.read(mpath)
    assert len(t_m) == len(t_j) and all(abs(a - b) < 1e-9 for a, b in zip(t_m, t_j)), "time grids differ"
    assert all(c in j for c in m), [c for c in m if c not in j][:5]
    perm = {c: C.deviation(j[c], m[c]) for c in m}
    wm = max((c for c in perm if perm[c][0] is not None), key=lambda c: perm[c][0])
    only = [c for c in j if c not in m]
    largest = max((max(abs(v) for v in j[c]) for c in only), default=0.0)
    print(f"against Octave: {len(m)} compartments compared; worst {wm}: rel {perm[wm][0]:.2e}, day {t_m[perm[wm][2]]:.0f}; "
          f"{len(only)} compartments only in AlgebraicPetri, largest value {largest:.3g}")
