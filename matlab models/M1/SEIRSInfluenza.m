global mu gamma beta N nu sigma;
mu = 0.00137;
gamma = 0.233;
beta = 0.5;
sigma = 0.67;
nu = 0.00274;
N = 50000;
S = 49900;
I = 100;
E = 0;
R = 0;

[T, Y] = resolve([S E I R]);

visualization(T,Y);
