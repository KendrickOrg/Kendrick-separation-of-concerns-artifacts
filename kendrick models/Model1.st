KModel SEIRS
    attribute: #(status in (S E I R));
    parameters: #(beta lambda gamma mu sigma nu);
    lambda: #(beta*I/N);
    equations: #(
         S:t=mu*N - lambda*S - mu*S + nu*R.
         E:t=lambda*S - sigma*E - mu*E.
         I:t=sigma*E - gamma*I - mu*I.
         R:t=gamma*I - mu*R - nu*R.).

Composition Influenza
    model: 'SEIRS'.

Scenario Scr1
    on: 'Influenza';
    mu: 0.00137;
    beta: 0.5;
    gamma: 0.233;
    sigma: 0.67;
    nu: 0.00274;
    S: 49900;
    I: 100.

Simulation InfluenzaSim
    solver: 'rungeKutta';
    scenario: 'Scr1';
    from: 0;
    to: 1500;
    step: 1.

Visualization InfluenzaViz
    plot: 'diagram';
    for: 'InfluenzaSim';
    xLabel: 'Time (days)'.
