#!/usr/bin/env python3
"""
Reruns the four Kendrick models with a step of a tenth of a day instead of one day and compares the
result, at the integer days, with the MATLAB trajectories (the measure of compare.py: largest deviation
over the integer days, relative to the peak of the MATLAB series). This is the step-refinement check of
Section 4.5: the deviations of compare.py are the discretization error of the fixed-step integrator and
drop with the step.

    python3 tools/compare/refine.py            (from the root of the repository; needs the jar and Java 23,
                                                 JAVA_HOME or java on the PATH, and the MATLAB trajectories)

Writes generated/trajectory-comparison-refined.json and prints a summary.
"""
import json, os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare as C

ROOT = C.ROOT
JAR = os.path.join(os.path.dirname(ROOT), "JKendrick", "target", "jkendrick.jar")
STEP = 0.1


def refined_trajectory(k, workdir):
    script = os.path.join(ROOT, "kendrick models", f"Model{k}.st")
    text = open(script, encoding="utf-8").read()
    assert text.count("step: 1.") == 1, f"Model{k}: one 'step: 1.' expected"
    refined = os.path.join(workdir, f"Model{k}.st")
    open(refined, "w", encoding="utf-8").write(text.replace("step: 1.", f"step: {STEP}."))
    out = os.path.join(workdir, f"Model{k}.csv")
    subprocess.run(["java", "-cp", JAR, "jKendrick.Kendrick", refined, "--csv", out], check=True,
                   stdout=subprocess.DEVNULL)
    t, cols = C.read(out)
    keep = [i for i, v in enumerate(t) if abs(v - round(v)) < 1e-6]   # the integer days
    return [t[i] for i in keep], {n: [s[i] for i in keep] for n, s in cols.items()}


def main():
    result = {"step": STEP}
    with tempfile.TemporaryDirectory() as workdir:
        for k in range(1, 5):
            t_k, kc = refined_trajectory(k, workdir)
            t_m, mc = C.read(os.path.join(C.MDIR, f"M{k}.csv"))
            assert len(t_k) == len(t_m), (len(t_k), len(t_m))
            common = [c for c in kc if c in mc]
            worst = None
            for c in common:
                rel, dev, at, peak = C.deviation(kc[c], mc[c])
                if rel is not None and (worst is None or rel > worst[1]):
                    worst = (c, rel, dev, peak, t_k[at])
            n = len(t_k)
            ak, am = C.aggregate(kc, n), C.aggregate(mc, n)
            agg = max(((key,) + C.deviation(ak[key], am[key])[:1] for key in am if key in ak), key=lambda x: x[1])
            result[f"Model{k}"] = {"compartments_compared": len(common), "max_relative_deviation": worst[1],
                                   "worst_compartment": worst[0],
                                   "worst_detail": {"absolute": worst[2], "peak": worst[3], "day": worst[4]},
                                   "aggregated_max_relative_deviation": agg[1], "aggregated_worst_series": agg[0]}
            print(f"Model{k} (step {STEP}): {len(common)} compartments, max relative deviation {worst[1]:.2e} "
                  f"on {worst[0]} (day {worst[4]:.0f}); aggregated {agg[1]:.2e} on {agg[0]}")
    out = os.path.join(ROOT, "generated", "trajectory-comparison-refined.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=1)
    print("written", out)


if __name__ == "__main__":
    main()
