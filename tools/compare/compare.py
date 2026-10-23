#!/usr/bin/env python3
"""
Compartment-by-compartment comparison of the Kendrick and MATLAB trajectories of Models 1-4
(Section 4.6 of the paper).

    java -cp <JKendrick>/target/jkendrick.jar jKendrick.Kendrick "kendrick models/Model<k>.st" \
         --csv generated/kendrick-trajectories/Model<k>.csv        (k = 1..4; RK4, step 1 day)
    octave-cli tools/compare/dump_matlab.m                          (ode45, RelTol 1e-8, integer days)
    python3 tools/compare/compare.py                                (from the root of the repository)

writes generated/trajectory-comparison.json and prints a summary. For every compartment that exists
in both versions, the measure is the largest |Kendrick - MATLAB| over the 1 501 integer days divided by
the peak of the MATLAB series (its largest value over time); for a compartment that exists only in
Kendrick (the isolated S and E of Model 4, which no transition reaches), it is the largest value the
compartment takes. The aggregated series per status and species (isolated included) and the total
population are reported as well, as in the earlier versions of the comparison.
"""
import csv, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KDIR = os.path.join(ROOT, "generated", "kendrick-trajectories")
MDIR = os.path.join(ROOT, "generated", "matlab-trajectories")
SPECIES = {"humans", "birds"}


def read(path):
    with open(path, newline="") as f:
        rows = list(csv.reader(f))
    names = rows[0][1:]
    t = [float(r[0]) for r in rows[1:]]
    cols = {n: [float(r[i + 1]) for r in rows[1:]] for i, n in enumerate(names)}
    return t, cols


def aggregate_key(name):
    parts = name.split("_")
    key = parts[0]
    if len(parts) > 1 and parts[1] in SPECIES:
        key += "_" + parts[1]
    return key


def aggregate(cols, n):
    agg = {}
    for name, series in cols.items():
        key = aggregate_key(name)
        acc = agg.setdefault(key, [0.0] * n)
        for i, v in enumerate(series):
            acc[i] += v
    return agg


def deviation(k, m):
    peak = max(m)
    dev = max(abs(a - b) for a, b in zip(k, m))
    at = max(range(len(k)), key=lambda i: abs(k[i] - m[i]))
    return (dev / peak if peak > 0 else None), dev, at, peak


def compare(k, matlab_file=None):
    t_k, kcols = read(os.path.join(KDIR, f"Model{k}.csv"))
    t_m, mcols = read(os.path.join(MDIR, matlab_file or f"M{k}.csv"))
    assert len(t_k) == len(t_m) and all(abs(a - b) < 1e-9 for a, b in zip(t_k, t_m)), "time grids differ"
    n = len(t_k)
    common = [c for c in kcols if c in mcols]
    only_k = [c for c in kcols if c not in mcols]
    only_m = [c for c in mcols if c not in kcols]
    assert not only_m, f"MATLAB compartments unknown to Kendrick: {only_m}"
    per = {}
    for c in common:
        rel, dev, at, peak = deviation(kcols[c], mcols[c])
        per[c] = {"relative": rel, "absolute": dev, "day": t_k[at], "peak": peak}
    worst = max((c for c in common if per[c]["relative"] is not None), key=lambda c: per[c]["relative"])
    agg_k, agg_m = aggregate(kcols, n), aggregate(mcols, n)
    agg = {}
    for key in agg_m:
        rel, dev, at, peak = deviation(agg_k[key], agg_m[key])
        agg[key] = {"relative": rel, "absolute": dev, "day": t_k[at], "peak": peak}
    worst_agg = max(agg, key=lambda key: agg[key]["relative"])
    tot_k = [sum(kcols[c][i] for c in kcols) for i in range(n)]
    tot_m = [sum(mcols[c][i] for c in mcols) for i in range(n)]
    pop = {
        "initial": tot_m[0],
        "kendrick_max_drift": max(abs(v - tot_k[0]) for v in tot_k),
        "matlab_max_drift": max(abs(v - tot_m[0]) for v in tot_m),
    }
    unreachable = {c: max(kcols[c]) for c in only_k}
    zero_peaks = [c for c in common if per[c]["relative"] is None]
    return {
        "compartments_compared": len(common),
        "compartments_only_in_kendrick": len(only_k),
        "max_relative_deviation": per[worst]["relative"],
        "worst_compartment": worst,
        "worst_detail": per[worst],
        "compartments_with_zero_peak": zero_peaks,
        "aggregated_max_relative_deviation": agg[worst_agg]["relative"],
        "aggregated_worst_series": worst_agg,
        "unreachable_in_kendrick_max_value": unreachable,
        "population": pop,
        "per_compartment": per,
        "aggregated": agg,
    }


def main():
    result = {}
    version_file = os.path.join(MDIR, "octave-version.txt")   # written by dump_matlab.m
    if os.path.exists(version_file):
        with open(version_file) as f:
            result["octave_version"] = f.read().strip()
    runs = [(1, None), (2, None), (3, None), (4, None)]
    for k, variant in runs:
        r = compare(k, variant)
        label = f"Model{k}" + ("_currentN" if variant else "")
        result[label] = r
        print(f"{label}: {r['compartments_compared']} compartments compared, "
              f"{r['compartments_only_in_kendrick']} only in Kendrick"
              + (" (MATLAB recomputing N from the current compartments)" if variant else ""))
        print(f"  max relative deviation {r['max_relative_deviation']:.2e} on {r['worst_compartment']} "
              f"(|diff| {r['worst_detail']['absolute']:.3g}, peak {r['worst_detail']['peak']:.5g}, "
              f"day {r['worst_detail']['day']:.0f})")
        print(f"  aggregated series: {r['aggregated_max_relative_deviation']:.2e} on {r['aggregated_worst_series']}")
        if r["unreachable_in_kendrick_max_value"]:
            print(f"  unreachable compartments, largest value: "
                  f"{max(r['unreachable_in_kendrick_max_value'].values()):.3g}")
        if r["compartments_with_zero_peak"]:
            print(f"  compartments with a zero MATLAB peak: {r['compartments_with_zero_peak']}")
        p = r["population"]
        print(f"  population {p['initial']:.6g}: drift {p['kendrick_max_drift']:.3g} (Kendrick), "
              f"{p['matlab_max_drift']:.3g} (MATLAB)")
    out = os.path.join(ROOT, "generated", "trajectory-comparison.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=1)
    print("written", out)


if __name__ == "__main__":
    main()
