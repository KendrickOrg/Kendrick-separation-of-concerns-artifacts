% Runs the MATLAB models M1..M4 of the paper under GNU Octave and writes their trajectories.
%
%     octave-cli tools/compare/dump_matlab.m          (from the root of the paper repository)
%
% For each model, the setup of its main script (matlab models/M<k>/SEIRSInfluenza.m, everything
% before the call of resolve) is executed as it is, and the ODE system of modelODEs.m is integrated
% with ode45 at RelTol = AbsTol = 1e-8, the solution being output at the integer days 0..1500.
% The result is generated/matlab-trajectories/M<k>.csv, one column per compartment, named as in
% the Kendrick models (S, S_humans, S_humans_1, S_humans_1_free, I_birds_3_isolated ...), so that
% tools/compare/compare.py can compare them with the trajectories written by JKendrick (--csv).
%
% Layout of the MATLAB state vectors (see the model files):
%   M1: [S E I R]                                   scalars
%   M2: [S(1:2) E(1:2) I(1:2) R(1:2)]              species order: humans, birds
%   M3: [S E I R], each an np x ns array reshaped column-major: index = p + (s-1)*np
%   M4: [S E I R IQ RQ], same layout; IQ and RQ are the isolated infectious and recovered,
%       so S and E have no isolated counterpart in MATLAB (those compartments are unreachable).
1;

function names = compartment_names(k, np, ns)
  species = {'humans', 'birds'};
  statuses = {'S', 'E', 'I', 'R'};
  names = {};
  if k == 1
    names = statuses;
  elseif k == 2
    for st = 1:4
      for s = 1:ns
        names{end+1} = sprintf('%s_%s', statuses{st}, species{s});
      end
    end
  else
    suffix = '';
    if k == 4
      suffix = '_free';
    end
    for st = 1:4
      for s = 1:ns
        for p = 1:np
          names{end+1} = sprintf('%s_%s_%d%s', statuses{st}, species{s}, p, suffix);
        end
      end
    end
    if k == 4
      for st = [3 4]
        for s = 1:ns
          for p = 1:np
            names{end+1} = sprintf('%s_%s_%d_isolated', statuses{st}, species{s}, p);
          end
        end
      end
    end
  end
end

function run_model(k, mdir, variantdir, out)
  addpath(mdir);
  if ~isempty(variantdir)
    addpath(variantdir);   % prepended: its modelODEs.m shadows the one of the model
  end
  clear -global
  txt = fileread(fullfile(mdir, 'SEIRSInfluenza.m'));
  cut = strfind(txt, '[T, Y] = resolve(');
  eval(txt(1:cut-1));
  arg = regexp(txt(cut:end), 'resolve\(([^)]*)\)', 'tokens', 'once');
  y0 = eval(arg{1});
  opts = odeset('RelTol', 1e-8, 'AbsTol', 1e-8);
  [T, Y] = ode45(@modelODEs, 0:1500, y0, opts);
  if k >= 3
    names = compartment_names(k, np, ns);
  else
    names = compartment_names(k, 0, 2);
  end
  assert(numel(names) == columns(Y), 'M%d: %d names for %d columns', k, numel(names), columns(Y));
  fid = fopen(out, 'w');
  fprintf(fid, 't,%s\n', strjoin(names, ','));
  for i = 1:rows(Y)
    fprintf(fid, '%g', T(i));
    fprintf(fid, ',%.12g', Y(i, :));
    fprintf(fid, '\n');
  end
  fclose(fid);
  printf('M%d: %d compartments, %d time points -> %s\n', k, columns(Y), rows(Y), out);
  if ~isempty(variantdir)
    rmpath(variantdir);
  end
  rmpath(mdir);
end

root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
outdir = fullfile(root, 'generated', 'matlab-trajectories');
if ~exist(outdir, 'dir')
  mkdir(outdir);
end
printf('GNU Octave %s\n', version());
fid = fopen(fullfile(outdir, 'octave-version.txt'), 'w');   % recorded with the trajectories, read by compare.py
fprintf(fid, 'GNU Octave %s\n', version());
fclose(fid);
for k = 1:4
  run_model(k, fullfile(root, 'matlab models', sprintf('M%d', k)), '', fullfile(outdir, sprintf('M%d.csv', k)));
end
