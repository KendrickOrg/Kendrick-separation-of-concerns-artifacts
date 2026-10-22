KModel SEIRS
    attribute: #(status in (S E I R));
    parameters: #(beta lambda gamma mu sigma nu);
    lambda: #(beta*I/N);
    equations: #(
         S:t=mu*N - lambda*S - mu*S + nu*R.
         E:t=lambda*S - sigma*E - mu*E.
         I:t=sigma*E - gamma*I - mu*I.
         R:t=gamma*I - mu*R - nu*R.).

KModel MultiSpecies
    attribute: #(species in (humans birds)).

KModel MetaPopulation
    attribute: #(zone in (range 1 15));
    parameters: #(rho);
    topology: #(ring oneWay);
    transitionRate: #(rho).

Composition Influenza
    model: 'SEIRS';
    model: 'MultiSpecies';
    model: 'MetaPopulation'.

Scenario Scr1
    on: 'Influenza';
    var: #((k in species) (i in species) (p in zone));
    mu_species: #(0.0000365 0.00137);
    beta_ki: #(#(0 0.025) #(0 0.5));
    gamma_species: #(0.25 0.233);
    sigma_species: #(0.5 0.67);
    nu: 0.00274;
    rho_species: #(0.03 0.1);
    lambda_pk: #(sum_ (i in species) beta_ki*I_ip/N_ip);
    S_species: #(75000 750000);
    S_birds_1: 49900;
    I_birds_1: 100.

Simulation InfluenzaSim
    solver: 'rungeKutta';
    scenario: 'Scr1';
    from: 0;
    to: 1500;
    step: 1.

Visualization InfluenzaViz
    plot: 'diagram';
    for: 'InfluenzaSim';
    data: #(I_birds_zone);
    legendTitle: 'Infectious birds';
    xLabel: 'Time (days)'.
