# The metapopulation concern: n zones on a one-way ring, with a migration (strata) transition from each
# zone to the next. Infection, disease progression, births and deaths are reflexive: local to a zone.
include("ontology.jl")

function ring_model(n)
    uwd = RelationDiagram(repeat([:Pop], n))
    zones = [add_junction!(uwd, :Pop, variable=Symbol("zone$i")) for i in 1:n]
    for (i, port) in enumerate(ports(uwd, outer=true))
        set_junction!(uwd, port, zones[i], outer=true)
    end
    names = Symbol[]
    for i in 1:n
        j = i % n + 1
        box = add_box!(uwd, [:Pop, :Pop], name=:strata)
        set_junction!(uwd, ports(uwd, box)[1], zones[i])
        set_junction!(uwd, ports(uwd, box)[2], zones[j])
        push!(names, Symbol("migration_$(i)_$(j)"))
        for (t, arity) in ((:infect, 4), (:disease, 2), (:birth, 1), (:death, 1))
            box = add_box!(uwd, fill(:Pop, arity), name=t)
            for port in ports(uwd, box)
                set_junction!(uwd, port, zones[i])
            end
            push!(names, Symbol("$(t)_$(i)"))
        end
    end
    oapply_typed(ontology, uwd, names)
end
