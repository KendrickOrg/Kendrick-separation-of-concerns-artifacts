# The multi-species concern: humans and birds. Individuals never change species, so there is no strata
# transition between the two; infection happens among birds and from birds to humans only, which is
# what the two infect boxes say (the first two ports are the susceptible and the infectious). Disease
# progression, migration, isolation, births and deaths are reflexive, within each species:
# add_reflexives adds them from the list of kinds of each species.
include("ontology.jl")

species_uwd = @relation (humans, birds) where (humans::Pop, birds::Pop) begin
    infect(birds, birds, birds, birds)
    infect(humans, birds, humans, birds)
end
species = oapply_typed(ontology, species_uwd, [:infect_BB, :infect_HB])
species = add_reflexives(species, [[:disease, :strata, :isolate, :birth, :death], [:disease, :strata, :isolate, :birth, :death]], ontology)
