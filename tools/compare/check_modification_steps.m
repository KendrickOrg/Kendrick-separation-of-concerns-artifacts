% Runs the two modification steps of Model 3 in MATLAB under GNU Octave (Section 5.5):
%   matlab models/M3-20zones   (20 zones instead of 15)
%   matlab models/M3-3species  (a third species)
% and prints the final state, so that the variants are known to run.
%
%     octave-cli tools/compare/check_modification_steps.m      (from the root of the repository)
1;
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
set(0, 'defaultfigurevisible', 'off');
for d = {'M3-20zones', 'M3-3species'}
  mdir = fullfile(root, 'matlab models', d{1});
  addpath(mdir);
  clear -global
  run(fullfile(mdir, 'SEIRSInfluenza.m'));
  printf('%s: %d compartments, day %g, total population %.6g\n', d{1}, columns(Y), T(end), sum(Y(end, :)));
  rmpath(mdir);
end
