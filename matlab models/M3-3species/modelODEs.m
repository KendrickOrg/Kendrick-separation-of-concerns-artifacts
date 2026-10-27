function res=modelODEs(t, compartments)
global mu gamma beta N nu sigma rho np ns ;
S = reshape(compartments(1: np*ns),[np ns]);
E = reshape(compartments(np*ns+1: 2*np*ns),[np ns]);
I = reshape(compartments(2*np*ns+1: 3*np*ns),[np ns]);
R = reshape(compartments(3*np*ns+1: end),[np ns]);
lambda = zeros(np, ns);
for p = 1:np
  for s = 1:ns
    lambda(p,s) = sum(beta(s,:,p).*I(p,:)./N(p,:));
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
dIdt = sigma.*E - gamma.*I - mu.*I + deltaI ;
dRdt = gamma.*I - mu.*R - nu.*R + deltaR ;
dSdt = reshape(dSdt ,[1 np * ns ]);
dEdt = reshape(dEdt ,[1 np * ns ]);
dIdt = reshape(dIdt ,[1 np * ns ]);
dRdt = reshape(dRdt ,[1 np * ns ]);
res = [dSdt dEdt dIdt dRdt]';
