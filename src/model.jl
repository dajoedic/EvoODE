# src/model.jl

"""
    make_model()

Erzeugt ein einfaches lineares 2D-Modell:

    du1 = p1*u1 + p2*u2
    du2 = p3*u1 + p4*u2
"""
function make_model()
    function f!(du, u, p, t)
        du[1] = p[1] * u[1] + p[2] * u[2]
        du[2] = p[3] * u[1] + p[4] * u[2]
    end
    return f!
end
