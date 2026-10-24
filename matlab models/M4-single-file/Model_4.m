function [t,pop] = Model_4(np,ns,mu,gamma,beta,sigma,nu,rho,delta,epsilon,N,I,MaxTime)
%
% Model_4( np, ns, mu, gamma, beta, sigma, nu, rho, delta, epsilon, N, I, MaxTime)
%      Model 4 of the paper (SEIRS, multi-species, metapopulation, isolation) in the layout of
% the MATLAB programs of Keeling and Rohani's book "Modeling Infectious Diseases in Humans and
% Animals": one file, a main function that sets the default parameters, integrates and plots,
% and a subfunction for the right-hand side that receives the parameters as arguments.
% The statements are those of ../M4 (four files, global parameters); the state is packed and
% unpacked with one reshape, as in their Program 7.2. Like ../M4, it does not check its parameters.

% Sets up default parameters if necessary.
if nargin == 0
   np = 15;
   ns = 2;
   mu = repmat([0.0000365 0.00137], np, 1);
   gamma = repmat([0.25 0.233], np, 1);
   beta = repmat([0 0.025; 0 0.5], [1 1 np ]);
   sigma = repmat([0.5 0.67], np, 1);
   nu = repmat(0.00274, np, ns);
   map = circshift(eye(np), 1); % one-way ring: flow from p to p+1
   rho = cat(3,map*0.03,map*0.1);
   delta = repmat(0.2, np, ns);
   epsilon = repmat(1, np, ns);
   N = repmat([5000 50000], np, 1);
   I = zeros(np, ns);
   p = 1;
   s = 2;
   I(p,s)=100;
   MaxTime = 1500;
end

S = N-I;
E = zeros(np, ns);
R = zeros(np, ns);
IQ = zeros(np, ns);
RQ = zeros(np, ns);
All = reshape([S E I R IQ RQ], 6*np*ns, 1);

% The main iteration
options = odeset('RelTol', 1e-8, 'AbsTol', 1e-8);
[t, pop] = ode45(@Diff_Model_4, [0 MaxTime], All, options, np, ns, mu, gamma, beta, sigma, nu, rho, delta, epsilon);

% Plots the total infectious of each species
res=zeros(length(t),2);
res(:,1)=sum(pop(:,2*np*ns+1:2*np*ns+np),2)+sum(pop(:,4*np*ns+1:4*np*ns+np),2); % free + isolated infectious humans
res(:,2)=sum(pop(:,2*np*ns+np+1:3*np*ns),2)+sum(pop(:,4*np*ns+np+1:5*np*ns),2); % free + isolated infectious birds
plot(t,res');
legend('Human','Bird');
xlabel('Time');
ylabel('Total Infectious');

% Calculates the differential rates used in the integration.
function dPop=Diff_Model_4(t, pop, np, ns, mu, gamma, beta, sigma, nu, rho, delta, epsilon)
S = reshape(pop(1: np*ns),[np ns]);
E = reshape(pop(np*ns+1: 2*np*ns),[np ns]);
I = reshape(pop(2*np*ns+1: 3*np*ns),[np ns]);
R = reshape(pop(3*np*ns+1: 4*np*ns),[np ns]);
IQ = reshape(pop(4*np*ns+1: 5*np*ns),[np ns]);
RQ = reshape(pop(5*np*ns+1: end),[np ns]);
N = S + E + I + R + IQ + RQ;
lambda = zeros(np, ns);
for p = 1:np
  for s = 1:ns
    lambda(p,s) = sum(beta(s,:,p).*I(p,:)./(N(p,:)-IQ(p,:)));
  end
end
deltaS = zeros(np,ns);
deltaE = zeros(np,ns);
deltaI = zeros(np,ns);
deltaR = zeros(np,ns);
for s = 1:ns
  deltaS(:,s) = rho(:,:,s)*S(:,s)-sum(rho(:,:,s))'.* S(:,s);
  deltaE(:,s) = rho(:,:,s)*E(:,s)-sum(rho(:,:,s))'.* E(:,s);
  deltaI(:,s) = rho(:,:,s)*I(:,s)-sum(rho(:,:,s))'.* I(:,s);
  deltaR(:,s) = rho(:,:,s)*R(:,s)-sum(rho(:,:,s))'.* R(:,s);
end
dSdt = mu.*N + nu.*R - lambda.*S - mu.*S + deltaS ;
dEdt = lambda.*S - sigma.*E - mu.*E + deltaE ;
dIdt = sigma.*E - gamma.*I - delta.*I - mu.*I + deltaI ;
dRdt = gamma.*I + epsilon.*RQ - mu.*R - nu.*R + deltaR ;
dIQdt = delta.*I - gamma.*IQ - mu.*IQ ;
dRQdt = gamma.*IQ - epsilon.*RQ - mu.*RQ ;
dPop = reshape([dSdt dEdt dIdt dRdt dIQdt dRQdt], 6*np*ns, 1);
