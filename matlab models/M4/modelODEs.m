function res=modelODEs(t, compartments)
global mu gamma beta nu sigma rho delta epsilon np ns ;
S = reshape(compartments(1: np*ns),[np ns]);
E = reshape(compartments(np*ns+1: 2*np*ns),[np ns]);
I = reshape(compartments(2*np*ns+1: 3*np*ns),[np ns]);
R = reshape(compartments(3*np*ns+1: 4*np*ns),[np ns]);
IQ = reshape(compartments(4*np*ns+1: 5*np*ns),[np ns]);
RQ = reshape(compartments(5*np*ns+1: end),[np ns]);
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
dSdt = reshape(dSdt ,[1 np * ns ]);
dEdt = reshape(dEdt ,[1 np * ns ]);
dIdt = reshape(dIdt ,[1 np * ns ]);
dRdt = reshape(dRdt ,[1 np * ns ]);
dIQdt = reshape(dIQdt ,[1 np * ns ]);
dRQdt = reshape(dRQdt ,[1 np * ns ]);
res = [dSdt dEdt dIdt dRdt dIQdt dRQdt]';
