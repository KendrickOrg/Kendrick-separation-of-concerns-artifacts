# The isolation concern of Model 4: free or isolated individuals. Isolation and release are the two
# isolate transitions. Infection, migration and births happen among free individuals only (an isolated
# individual neither infects nor is infected, does not migrate, and newborns are free); disease
# progression and deaths happen in both states. Which statuses are isolated or released, and at which
# rates, is decided by the rate function of the assembly file (delta for I, epsilon for R).
include("ontology.jl")

isolation_uwd = @relation (free, isolated) where (free::Pop, isolated::Pop) begin
    isolate(free, isolated)
    isolate(isolated, free)
    infect(free, free, free, free)
    disease(free, free)
    disease(isolated, isolated)
    strata(free, free)
    birth(free)
    death(free)
    death(isolated)
end
isolation = oapply_typed(ontology, isolation_uwd,
    [:isolation, :release, :infect_free, :disease_free, :disease_isolated, :strata_free, :birth_free, :death_free, :death_isolated])
