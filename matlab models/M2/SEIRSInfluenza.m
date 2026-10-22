global mu gamma beta N nu sigma ns;
mu = [0.0000365 0.00137];
gamma = [0.25 0.233];
beta = [0 0.025;0 0.5];
sigma = [0.5 0.67];
nu = 0.00274;
ns = 2;
N = [5000 50000];
S = [5000 49900];
I = [0 100];
E = [0 0];
R = [0 0];

[T, Y] = resolve([S E I R]);

visualization(T,Y);
