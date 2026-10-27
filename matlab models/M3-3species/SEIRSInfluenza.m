global mu gamma beta N nu sigma rho np ns;
np = 15;
ns = 3;
mu = repmat([0.0000365 0.00137 0.00137], np, 1);
gamma = repmat([0.25 0.233 0.233], np, 1);
beta = repmat([0 0.025 0; 0 0.5 0; 0 0.025 0], [1 1 np ]);
sigma = repmat([0.5 0.67 0.67], np, 1);
nu = repmat(0.00274, np, ns);
map = circshift(eye(np), 1); % one-way ring: flow from p to p+1
rho = cat(3,map*0.03,map*0.1,map*0.03);
N = repmat([5000 50000 5000], np, 1);
I = zeros(np, ns);
p = 1;
s = 2;
I(p,s)=100;
S = N-I;
E = zeros(np, ns);
R = zeros(np, ns);

S = reshape(S,[1 ns * np ]);
E = reshape(E,[1 ns * np ]);
I = reshape(I,[1 ns * np ]);
R = reshape(R,[1 ns * np ]);
[T, Y] = resolve([S E I R]);

visualization(T,Y);
