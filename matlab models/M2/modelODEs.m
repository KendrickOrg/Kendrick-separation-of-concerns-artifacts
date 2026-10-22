function res=modelODEs(t, compartments)
global mu gamma beta N nu sigma ns;
S = compartments(1:2)'; % row vector (ode45 passes a column)
E = compartments(3:4)';
I = compartments(5:6)';
R = compartments(7:8)';
lambda=zeros(1,ns);
for s=1:ns
   lambda(s) = sum(beta(s,:).*I./N);
end
dSdt = mu.*N - lambda.*S - mu.*S + nu.*R;
dEdt = lambda.*S - sigma.*E - mu.*E;
dIdt = sigma.*E - gamma.*I - mu.*I;
dRdt = gamma.*I - mu.*R - nu.*R;
res = [dSdt dEdt dIdt dRdt]';
