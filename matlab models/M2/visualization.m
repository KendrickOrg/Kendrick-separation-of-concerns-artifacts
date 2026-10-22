function res=visualization(T,Y)
plot(T,Y(:,5:6));
legend('Human','Bird');
xlabel('Time');
ylabel('Total Infectious');
