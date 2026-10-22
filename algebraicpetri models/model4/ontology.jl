# The type system of infectious-disease models, AlgebraicPetri's "infectious ontology" (one population
# type, infection, disease progression and movement between strata), extended with births and deaths,
# which the models of the paper have, and with isolation (entering or leaving isolation), which Model 4
# adds: a movement between strata would combine with the migrations of the ring in the typed product.
# Every concern is a Petri net typed over this net.
using AlgebraicPetri, AlgebraicPetri.TypedPetri
using Catlab

const ontology = LabelledPetriNet(
    [:Pop],
    :infect => ((:Pop, :Pop) => (:Pop, :Pop)),
    :disease => (:Pop => :Pop),
    :strata => (:Pop => :Pop),
    :birth => (() => :Pop),
    :death => (:Pop => ()),
    :isolate => (:Pop => :Pop),
)
