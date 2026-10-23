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

# The kinds of events of the ontology that a concern does not describe itself happen within each of
# its states: with_reflexives adds them as reflexive transitions, computed from the ontology, so that
# a concern need not list the kinds of events of the other concerns and is unchanged when a kind is
# added to the ontology.
function with_reflexives(typed, ontology)
    used = Set(tname(ontology, ix) for ix in collect(typed[:T]))
    others = [kind for kind in tnames(ontology) if kind ∉ used]
    add_reflexives(typed, [others for _ in 1:ns(dom(typed))], ontology)
end
