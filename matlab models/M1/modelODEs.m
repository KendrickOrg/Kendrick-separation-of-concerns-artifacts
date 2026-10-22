function res=modelODEs(t, compartments)
global mu gamma beta N nu sigma;
S = compartments(1);
E = compartments(2);
I = compartments(3);
R = compartments(4);
dSdt = mu*N - beta*S*I/N - mu*S + nu*R;
dEdt = beta*S*I/N - sigma*E - mu*E;
dIdt = sigma*E - gamma*I - mu*I;
dRdt = gamma*I - mu*R - nu*R;
res = [dSdt dEdt dIdt dRdt]';
