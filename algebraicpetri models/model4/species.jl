# The multi-species concern: humans and birds. Individuals never change species, so there is no strata
# transition between the two; infection happens among birds and from birds to humans only, which is
# what the two infect boxes say (the first two ports are the susceptible and the infectious). Disease
# progression, migration, isolation, births and deaths are reflexive: they happen within each species.
include("ontology.jl")

species_uwd = @relation (humans, birds) where (humans::Pop, birds::Pop) begin
    infect(birds, birds, birds, birds)
    infect(humans, birds, humans, birds)
    disease(humans, humans)
    disease(birds, birds)
    strata(humans, humans)
    strata(birds, birds)
    isolate(humans, humans)
    isolate(birds, birds)
    birth(humans)
    birth(birds)
    death(humans)
    death(birds)
end
species = oapply_typed(ontology, species_uwd,
    [:infect_BB, :infect_HB, :disease_H, :disease_B, :strata_H, :strata_B, :isolate_H, :isolate_B, :birth_H, :birth_B, :death_H, :death_B])
