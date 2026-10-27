#!/bin/sh
# Regenerates figures/Kcolorized.pdf and figures/Mcolorized.pdf from the model files.
# Needs python3 with playwright (pip install playwright; playwright install chromium).
set -e
cd "$(dirname "$0")/../.."
python tools/colorize/colorize.py kendrick "kendrick models/Model3.st" tools/colorize/K.html 2
# Figure 3 shows the main script and the ODE function; the three-line solver call and the visualization are omitted
python tools/colorize/colorize.py matlab "matlab models/M3" tools/colorize/M.html 2 SEIRSInfluenza.m modelODEs.m
python tools/colorize/topdf.py "$PWD/tools/colorize/K.html" "$PWD/figures/Kcolorized.pdf"
python tools/colorize/topdf.py "$PWD/tools/colorize/M.html" "$PWD/figures/Mcolorized.pdf"
