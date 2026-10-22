# The SEIRS concern with vital dynamics, as a Petri net typed over the ontology: infection S + I -> E + I,
# incubation, recovery, loss of immunity, a birth into S and a death from every state. A reflexive
# strata transition on every state lets a spatial stratification move individuals without changing
# their status, and a reflexive isolate transition lets the isolation concern isolate or release them.
include("ontology.jl")

seirs_uwd = @relation (S, E, I, R) where (S::Pop, E::Pop, I::Pop, R::Pop) begin
    infect(S, I, E, I)
    disease(E, I)
    disease(I, R)
    disease(R, S)
    birth(S)
    death(S)
    death(E)
    death(I)
    death(R)
end
seirs = oapply_typed(ontology, seirs_uwd,
    [:infection, :incubation, :recovery, :loss, :birth, :death_S, :death_E, :death_I, :death_R])
seirs = add_reflexives(seirs, [[:strata, :isolate], [:strata, :isolate], [:strata, :isolate], [:strata, :isolate]], ontology)
