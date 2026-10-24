function res=visualization(T,Y)
global np ns;
res=zeros(length(T),2);
res(:,1)=sum(Y(:,2*np*ns+1:2*np*ns+np),2)+sum(Y(:,4*np*ns+1:4*np*ns+np),2); % free + isolated infectious humans
res(:,2)=sum(Y(:,2*np*ns+np+1:3*np*ns),2)+sum(Y(:,4*np*ns+np+1:5*np*ns),2); % free + isolated infectious birds
plot(T,res');
legend('Human','Bird');
xlabel('Time');
ylabel('Total Infectious');
