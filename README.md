# Artifacts of "A Formal Approach to Separation of Concerns in Epidemiology Modeling"

This repository holds everything needed to reproduce the measurements and the numerical comparisons of the
paper, submitted to Software and Systems Modeling (SoSyM): the models in the three languages, the scripts
that compute the metrics of Section 5 and compare the trajectories of Section 4.5, and their outputs.
The reference implementation of the Kendrick language is a separate repository,
https://github.com/KendrickOrg/JKendrick; the results of the paper were obtained with its release v0.2.5, archived at
https://doi.org/10.5281/zenodo.23689100 (v0.2.4 was https://doi.org/10.5281/zenodo.23613533, v0.2.3 was https://doi.org/10.5281/zenodo.23602490, v0.2.2 was https://doi.org/10.5281/zenodo.23601380, v0.2.1 was https://doi.org/10.5281/zenodo.23590968). This repository is
archived on Zenodo at https://doi.org/10.5281/zenodo.23588339, a DOI that always resolves to the latest
release; the record lists every release with its own DOI.

## Contents

- `kendrick models/`: the four Kendrick models of the paper, `Model1.st` to `Model4.st` (SEIRS; plus two
  species; plus fifteen zones on a one-way ring; plus isolation of the infectious), in the syntax of
  Section 4, described in `SYNTAX.md`. `M1a.kendrick` is the SIR example of the Kendrick wiki, in the same syntax.
  `Model3-20zones.st` and `Model3-3species.st` are the two modification steps of Model 3 (Section 5.5: 20 zones
  instead of 15; a third species with placeholder values); `matlab models/M3-20zones` and `M3-3species` are their
  MATLAB counterparts. `metrics.py` measures the steps (`generated/modification-effort.tex`, key `modifications` of
  `metrics.json`); `tools/compare/check_modification_steps.m` runs the MATLAB variants under Octave.
- `matlab models/M1` to `M4`: the same four models written by hand in MATLAB, four files each (main
  script `SEIRSInfluenza.m`, `modelODEs.m`, `resolve.m`, `visualization.m`). They run under GNU Octave.
  `M4` is the corrected version of Section 4.5 (the ODE function recomputes `N` from the current compartments).
  `M4-single-file/Model_4.m` is Model 4 in the layout of Keeling and Rohani's MATLAB programs (Section 6.2):
  one file, a main function that sets the default parameters, integrates and plots, and a subfunction for
  the right-hand side that receives the parameters as arguments. `metrics.json` gives its measures under the
  key `matlab_single_file`; `tools/compare/check_single_file.m` checks that it computes the trajectory of `M4`.
- `algebraicpetri models/`: Model 3 in AlgebraicPetri (Julia): `ontology.jl` (the type system, with
  births and deaths added), `seirs.jl`, `species.jl`, `ring.jl` (one typed Petri net per concern) and
  `model3.jl` (typed product, rates as functions of the state, initial state, integration, trajectory);
  the reflexive transitions of each net are computed from the ontology by `with_reflexives` (ontology.jl).
  `model4/` is the isolation step applied to these files (Section 5.5.3): `isolation.jl` is the new
  concern, the ontology gains the event kind `isolate`, the three other concern nets are unchanged,
  `model4.jl` is the assembly; the step changes 12 statements and adds 24, from 117 to 141
  (`metrics.json`, key `algebraicpetri_step`). Model 3 agrees with the Kendrick trajectory to 2.6e-4 and
  Model 4 to 4.2e-3 of the peak (`compare_algebraicpetri.py`).
  `Project.toml` and `Manifest.toml` pin the package versions.
- `tools/metrics/metrics.py`: computes every number of Section 5 (traces, scattering, dependencies, change
  scope) from the model sources and writes `generated/*.tex`, `generated/metrics.json` and
  `figures/dependency-graph.pdf`. The attribution of identifiers to concerns is the table in the script,
  shared with `tools/colorize/colorize.py`, which draws Figures 3 and 4.
- `tools/compare/`: `dump_matlab.m` runs the MATLAB models under Octave (ode45, RelTol 1e-8, one point per
  day); `compare.py` compares them compartment by compartment with the trajectories written by JKendrick
  and writes `generated/trajectory-comparison.json` (Section 4.5); `refine.py` reruns the four Kendrick
  models with a step of a tenth of a day and writes `generated/trajectory-comparison-refined.json` (the
  step-refinement check of Section 4.5); `compare_algebraicpetri.py [3|4]` does the same for the
  AlgebraicPetri models (Sections 5.3 and 5.5.3). `dump_matlab.m` records the Octave version in
  `generated/matlab-trajectories/octave-version.txt`, which `compare.py` copies into its output.
  `check_single_file.m` runs `matlab models/M4-single-file/Model_4.m` and compares its state at day 1500 with
  that of `M4` (maximum relative difference 4.4e-12).
- `generated/`: the outputs. The tables of Section 5 (`scattering.tex`, `scattering3.tex`, `size-metrics.tex`,
  `dependency-metrics.tex`, `change-effort.tex`), `metrics.json` (every number, with the attribution of each
  statement), `trajectory-comparison.json`, and the trajectories of every model in every language
  (`kendrick-trajectories/`, `matlab-trajectories/`, `algebraicpetri-trajectories/`, one CSV per model, one
  column per compartment, one row per day). The trajectories are included so that the comparisons can be
  checked without Octave or Julia; the commands below regenerate them.
- `figures/`: the three generated figures of the paper (`Mcolorized.pdf` and `Kcolorized.pdf`, the colorized
  Model 3 in MATLAB and Kendrick; `dependency-graph.pdf`, the dependency graphs of Model 4).

## Reproducing

Prerequisites: Python 3 with `matplotlib`; a JDK 23 (the release of JKendrick's `pom.xml`) and Maven for JKendrick; GNU Octave for the MATLAB
trajectories; Julia 1.9+ for AlgebraicPetri; `playwright` with `playwright install chromium` for the
colorized figures only. On Windows, Octave and Julia are not put on the PATH by their installers.

    git clone https://github.com/KendrickOrg/Kendrick-separation-of-concerns-artifacts.git artifacts
    git clone https://github.com/KendrickOrg/JKendrick.git
    cd JKendrick && git checkout v0.2.5 && mvn package && cd ../artifacts     # target/jkendrick.jar, the tests
    python tools/metrics/metrics.py                       # generated/*.tex, metrics.json, figures/dependency-graph.pdf
    for k in 1 2 3 4; do java -cp ../JKendrick/target/jkendrick.jar jKendrick.Kendrick "kendrick models/Model$k.st" --csv generated/kendrick-trajectories/Model$k.csv; done
    octave-cli tools/compare/dump_matlab.m                # generated/matlab-trajectories/M1..M4.csv
    octave-cli tools/compare/check_single_file.m          # Model 4 in one file against M4 (Section 6.2)
    octave-cli tools/compare/check_modification_steps.m   # the two modification steps of Model 3 run (Section 5.5)
    python tools/compare/compare.py                       # generated/trajectory-comparison.json (Section 4.5)
    python tools/compare/refine.py                        # generated/trajectory-comparison-refined.json (Section 4.5)
    julia --project="algebraicpetri models" -e "using Pkg; Pkg.instantiate()"   # once
    julia --project="algebraicpetri models" "algebraicpetri models/model3.jl"       # generated/algebraicpetri-trajectories/Model3.csv
    julia --project="algebraicpetri models" "algebraicpetri models/model4/model4.jl"   # generated/algebraicpetri-trajectories/Model4.csv
    python tools/compare/compare_algebraicpetri.py        # Model 3 (Section 5.3); add 4 for Model 4 (Section 5.5.3)
    bash tools/colorize/make-figures.sh                   # figures/Mcolorized.pdf and Kcolorized.pdf

Running `metrics.py` on this repository reproduces the committed `generated/*.tex` and `metrics.json`
byte for byte.

## Parameter values

The values are those of the parameter table of the paper (Section 5.2): Arino et al. 2007 (Mathematical Biosciences 206:46-60),
Section 5, with the transmission rate raised to beta_BB = 0.5 (their 0.24 gives R0 = 1.02 and no epidemic);
the isolation rate delta = 0.2 per day from Martcheva 2015 (Table 9.5) and the release rate epsilon = 1 per
day by convention. Fifteen zones on a one-way ring, 5000 humans and 50000 birds per zone, 100 infectious
birds in zone 1 at time 0, 1500 days.

## License

MIT, see `LICENSE`.
