# The multi-species concern: humans and birds. Individuals never change species, so there is no strata
# transition between the two; infection happens among birds and from birds to humans only, which is
# what the two infect boxes say (the first two ports are the susceptible and the infectious). The other
# kinds of events (disease progression, migration, births, deaths) happen within each species: they are
# the reflexive transitions that with_reflexives computes from the ontology.
include("ontology.jl")

species_uwd = @relation (humans, birds) where (humans::Pop, birds::Pop) begin
    infect(birds, birds, birds, birds)
    infect(humans, birds, humans, birds)
end
species = oapply_typed(ontology, species_uwd, [:infect_BB, :infect_HB])
species = with_reflexives(species, ontology)
