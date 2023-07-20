import pybamm
import numpy as np
import matplotlib.pylab as plt
import importlib

output_variables = [
    "Voltage [V]",
    "Time [min]",
    "Current [A]",
]
#output_variables = []
all_vars = False

input_parameters = {
    "Current function [A]": 0.680616,
    "Separator porosity": 1.0,
}

# check for loading errors
idaklu_spec = importlib.util.find_spec("pybamm.solvers.idaklu")
idaklu = importlib.util.module_from_spec(idaklu_spec)
idaklu_spec.loader.exec_module(idaklu)

# construct model
# pybamm.set_logging_level("INFO")
model = pybamm.lithium_ion.DFN()
# model.convert_to_format = 'jax'
geometry = model.default_geometry
param = model.default_parameter_values
param.update({key: "[input]" for key in input_parameters})
param.process_model(model)
param.process_geometry(geometry)
n = 100  # control the complexity of the geometry (increases number of solver states)
var_pts = {"x_n": n, "x_s": n, "x_p": n, "r_n": 10, "r_p": 10}
mesh = pybamm.Mesh(geometry, model.default_submesh_types, var_pts)
disc = pybamm.Discretisation(mesh, model.default_spatial_methods)
disc.process_model(model)
t_eval = np.linspace(0, 3600, 100)

options = {
    'linear_solver': 'SUNLinSol_KLU',
    'jacobian': 'sparse',
    'num_threads': 4,
}

if all_vars:
    output_variables = [m for m, (k, v) in
                        zip(model.variable_names(), model.variables.items())
                        if not isinstance(v, pybamm.ExplicitTimeIntegral)]
    left_out = [m for m, (k, v) in
                zip(model.variable_names(), model.variables.items())
                if isinstance(v, pybamm.ExplicitTimeIntegral)]
    print("ExplicitTimeIntegral variables:")
    print(left_out)

print("output_variables:")
print(output_variables)
print("\nInput parameters:")
print(input_parameters)

solver = pybamm.IDAKLUSolver(
    atol=1e-8, rtol=1e-8,
    options=options,
    output_variables=output_variables,
)

sol = solver.solve(
    model,
    t_eval,
    inputs=input_parameters,
    calculate_sensitivities=True,
)

print(f"Solve time: {sol.solve_time.value*1000} msecs")

if True:
    plot_allvars = False
    if not output_variables:
        plot_allvars = True
        output_variables = [
            "Voltage [V]",
            "Time [min]",
            "Current [A]",
        ]
    fig, axs = plt.subplots(len(output_variables), len(input_parameters)+1)
    for k, var in enumerate(output_variables):
        # Solution variables currently use different classes/calls
        if not input_parameters:
            axs[k].plot(t_eval, sol[var](t_eval))
        else:
            axs[k,0].plot(t_eval, sol[var](t_eval))
            for paramk, param in enumerate(list(input_parameters.keys())):
                axs[k,paramk+1].plot(t_eval, sol[var].sensitivities[param])
    plt.tight_layout()
    plt.show()
