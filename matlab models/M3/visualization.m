function res=visualization(T,Y)
global mu gamma beta N nu sigma rho np ns;
res=zeros(length(T),2);
res(:,1)=sum(Y(:,2*np*ns+1:2*np*ns+np),2);
res(:,2)=sum(Y(:,2*np*ns+np+1:3*np*ns),2);
plot(T,res');
legend('Human','Bird');
xlabel('Time');
ylabel('Total Infectious');
