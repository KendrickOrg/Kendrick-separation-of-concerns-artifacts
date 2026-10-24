% Checks that matlab models/M4-single-file/Model_4.m, Model 4 in the layout of Keeling and Rohani's
% programs, computes the trajectory of the four-file version matlab models/M4.
%
%     octave-cli tools/compare/check_single_file.m      (from the root of the repository,
%                                                        after tools/compare/dump_matlab.m)
%
% Model_4 integrates with ode45 at RelTol = AbsTol = 1e-8 on [0 1500], as dump_matlab.m does for M4
% on the integer days 0..1500; the two states at day 1500 are compared.
1;
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(root, 'matlab models', 'M4-single-file'));
set(0, 'defaultfigurevisible', 'off');
[t, pop] = Model_4();
ref = dlmread(fullfile(root, 'generated', 'matlab-trajectories', 'M4.csv'), ',', 1, 0);
assert(abs(t(end) - 1500) < 1e-9 && abs(ref(end, 1) - 1500) < 1e-9);
last = pop(end, :);
expected = ref(end, 2:end);
% the four-file state has no isolated S and E: same column order, S E I R IQ RQ in both
assert(numel(last) == numel(expected), '%d against %d compartments', numel(last), numel(expected));
d = max(abs(last - expected) ./ max(abs(expected), 1));
printf('Model_4 (single file) against M4 (four files), day 1500: %d compartments, max relative difference %.3g\n', numel(last), d);
