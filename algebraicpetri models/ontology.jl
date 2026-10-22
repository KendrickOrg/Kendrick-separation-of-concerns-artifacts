# The type system of infectious-disease models, AlgebraicPetri's "infectious ontology" (one population
# type, infection, disease progression and movement between strata), extended with births and deaths,
# which the models of the paper have. Every concern is a Petri net typed over this net.
using AlgebraicPetri, AlgebraicPetri.TypedPetri
using Catlab

const ontology = LabelledPetriNet(
    [:Pop],
    :infect => ((:Pop, :Pop) => (:Pop, :Pop)),
    :disease => (:Pop => :Pop),
    :strata => (:Pop => :Pop),
    :birth => (() => :Pop),
    :death => (:Pop => ()),
)
