# Model 3 of the paper (SEIRS, two species, fifteen zones on a one-way ring) in AlgebraicPetri: the
# stratified product of the three concerns, then the rates and initial populations of Table 2, the
# integration over 1500 days and the trajectory in the compartment names of the Kendrick version.
#
#     julia --project="algebraicpetri models" "algebraicpetri models/model3.jl"      (from the root of the repository)
#
# Petri nets are mass-action: the force of infection beta*I/N and the births mu*N are encoded with the
# population N of each zone and species folded into the rate constants, which is exact here because
# every local population is stationary (births balance deaths and the ring is balanced).
include("seirs.jl")
include("species.jl")
include("ring.jl")
using OrdinaryDiffEq

const np = 15
model = typed_product([seirs, species, ring_model(np)])
net = dom(model)
println("Model 3: ", ns(net), " places, ", nt(net), " transitions")

# ---- values of Table 2 (per day), indexed by species
beta = Dict(:infect_BB => 0.5, :infect_HB => 0.025)          # beta_ki: k the susceptible, i the infectious
infectious_of = Dict(:infect_BB => :birds, :infect_HB => :birds)
mu = Dict(:humans => 0.0000365, :birds => 0.00137)
sigma = Dict(:humans => 0.5, :birds => 0.67)
gamma = Dict(:humans => 0.25, :birds => 0.233)
nu = 0.00274
rho = Dict(:humans => 0.03, :birds => 0.1)
N0 = Dict(:humans => 5000.0, :birds => 50000.0)             # population of each zone and species, stationary

# The species of a transition, read on its first input place, or on its first output place for a birth:
# the reflexive transitions that add_reflexives creates are all named by their kind, so the species
# can only be read on the place.
function species_of(t)
    ins = incident(net, t, :it)
    place = isempty(ins) ? net[first(incident(net, t, :ot)), :os] : net[first(ins), :is]
    sname(net, place)[2]
end

function rate(t)
    d, k, z = tname(net, t)             # the SEIRS, species and ring components of the transition
    s = species_of(t)
    d == :infection && return beta[k] / N0[infectious_of[k]]
    d == :incubation && return sigma[s]
    d == :recovery && return gamma[s]
    d == :loss && return nu
    d == :birth && return mu[s] * N0[s]
    startswith(String(d), "death") && return mu[s]
    startswith(String(d), "strata") && return rho[s]
    error("no rate for $(tname(net, t))")
end
p = [rate(t) for t in 1:nt(net)]

# ---- initial state: 5000 humans and 50000 birds per zone, 100 infectious birds in zone 1
function initial(label)
    status, k, z = label
    if status == :S
        return N0[k] - (k == :birds && z == :zone1 ? 100.0 : 0.0)
    elseif status == :I
        return k == :birds && z == :zone1 ? 100.0 : 0.0
    end
    0.0
end
u0 = [initial(sname(net, s)) for s in 1:ns(net)]

prob = ODEProblem(vectorfield(PetriNet(net)), u0, (0.0, 1500.0), p)   # unlabelled copy: same order, integer indices
sol = solve(prob, Tsit5(), reltol=1e-8, abstol=1e-8, saveat=0:1500)

# ---- trajectory, in the compartment names of the Kendrick version (S_humans_1 ...)
name(label) = string(label[1], "_", label[2], "_", replace(String(label[3]), "zone" => ""))
out = joinpath(@__DIR__, "..", "generated", "algebraicpetri-trajectories")
mkpath(out)
open(joinpath(out, "Model3.csv"), "w") do f
    println(f, "t,", join([name(sname(net, s)) for s in 1:ns(net)], ","))
    for (i, t) in enumerate(sol.t)
        println(f, t, ",", join(sol.u[i], ","))
    end
end
println("written ", joinpath(out, "Model3.csv"))
