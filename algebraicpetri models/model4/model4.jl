# Model 4 of the paper (SEIRS, two species, fifteen zones on a one-way ring, isolation of the infectious)
# in AlgebraicPetri: the stratified product of the four concerns, then the rates and initial populations
# of Table 2, the integration over 1500 days and the trajectory in the compartment names of the Kendrick
# version. This folder is the evolution step S3 applied to the files of Model 3 (../*.jl): compare the
# two folders to see what the step changes.
#
#     julia --project="algebraicpetri models" "algebraicpetri models/model4/model4.jl"      (from the root of the repository)
#
# Petri nets are mass-action: the force of infection beta*I/N and the births mu*N are encoded with the
# population N of each zone and species folded into the rate constants. Model 4 makes this an
# approximation: isolated individuals do not migrate, so the local populations drift, and the Kendrick
# version divides by the current N_ip - I_ip_isolated.
include("seirs.jl")
include("species.jl")
include("ring.jl")
include("isolation.jl")
using OrdinaryDiffEq

const np = 15
model = typed_product([seirs, species, ring_model(np), isolation])
net = dom(model)
println("Model 4: ", ns(net), " places, ", nt(net), " transitions")

# ---- values of Table 2 (per day), indexed by species
beta = Dict(:infect_BB => 0.5, :infect_HB => 0.025)          # beta_ki: k the susceptible, i the infectious
infectious_of = Dict(:infect_BB => :birds, :infect_HB => :birds)
mu = Dict(:humans => 0.0000365, :birds => 0.00137)
sigma = Dict(:humans => 0.5, :birds => 0.67)
gamma = Dict(:humans => 0.25, :birds => 0.233)
nu = 0.00274
rho = Dict(:humans => 0.03, :birds => 0.1)
delta = 0.2                                                   # isolation of the infectious
epsilon = 1.0                                                 # release of the recovered
N0 = Dict(:humans => 5000.0, :birds => 50000.0)             # population of each zone and species at time 0

# A place of a transition, its first input, or its first output for a birth, whose label gives the
# status, the species and the isolation status of the individual: the reflexive transitions that
# add_reflexives creates are all named by their kind, so these can only be read on the place.
function place_of(t)
    ins = incident(net, t, :it)
    place = isempty(ins) ? net[first(incident(net, t, :ot)), :os] : net[first(ins), :is]
    sname(net, place)
end

function rate(t)
    d, k, z, q = tname(net, t)          # the SEIRS, species, ring and isolation components of the transition
    status, s, _, iso = place_of(t)
    d == :infection && return beta[k] / N0[infectious_of[k]]
    d == :incubation && return sigma[s]
    d == :recovery && return gamma[s]
    d == :loss && return iso == :free ? nu : 0.0                 # isolated individuals keep their immunity
    d == :birth && return mu[s] * N0[s]
    startswith(String(d), "death") && return mu[s]
    startswith(String(d), "strata") && return rho[s]
    d == :isolate && q == :isolation && return status == :I ? delta : 0.0
    d == :isolate && q == :release && return status == :R ? epsilon : 0.0
    error("no rate for $(tname(net, t))")
end
p = [rate(t) for t in 1:nt(net)]

# ---- initial state: 5000 humans and 50000 birds per zone, all free, 100 infectious birds in zone 1
function initial(label)
    status, k, z, iso = label
    iso == :free || return 0.0
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

# ---- trajectory, in the compartment names of the Kendrick version (S_humans_1_free ...)
name(label) = string(label[1], "_", label[2], "_", replace(String(label[3]), "zone" => ""), "_", label[4])
out = joinpath(@__DIR__, "..", "..", "generated", "algebraicpetri-trajectories")
mkpath(out)
open(joinpath(out, "Model4.csv"), "w") do f
    println(f, "t,", join([name(sname(net, s)) for s in 1:ns(net)], ","))
    for (i, t) in enumerate(sol.t)
        println(f, t, ",", join(sol.u[i], ","))
    end
end
println("written ", joinpath(out, "Model4.csv"))
