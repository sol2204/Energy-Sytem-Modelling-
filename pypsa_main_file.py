import pypsa
print(pypsa.__version__)
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

network = pypsa.Network()

# 1) Add buses first
network.add("Bus", "bus 1", carrier="AC")
network.add("Bus", "bus 2", carrier="AC")

# 2) Add components that reference buses
network.add("Generator", "solar_plant", bus="bus 1", p_nom=200, marginal_cost=0, carrier="solar")
network.add("Generator", "wind_farm", bus="bus 1", p_nom=120, marginal_cost=0, carrier="wind")
network.add("Generator", "natural_gas_plant", bus="bus 1", p_nom=40, marginal_cost=50, carrier="gas")

network.add("Line", "line 1", bus0="bus 1", bus1="bus 2", r=0.01, x=0.1, s_nom=100, carrier="AC")

network.add("Load", "load", bus="bus 2", p_set=50)

# 3) Snapshots
hours = pd.date_range("2024-01-01 00:00:00", "2024-01-01 23:00:00", freq="h")
network.set_snapshots(hours)

# 4) Solar + wind availability (p.u.)
angle_range = np.linspace(-np.pi/2, 3*np.pi/2, len(hours))   # FIXED
solar_output = np.maximum(0, np.sin(angle_range))

np.random.seed(0)
wind_output = np.random.normal(0.5, 0.2, len(hours))
wind_output = np.clip(wind_output, 0.2, 1.0)

# 5) Assign to generators_t.p_max_pu
network.generators_t.p_max_pu = pd.DataFrame(
    {"solar_plant": solar_output, "wind_farm": wind_output},
    index=hours
)


network.optimize(network.snapshots, solver_name="glpk")
results = network.generators_t.p
print(results)

fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

# --- Top plot: Generation dispatch ---
axes[0].plot(hours, 50 * np.ones(len(hours)), label="Demand")
axes[0].plot(hours, results["solar_plant"], label="Solar")
axes[0].plot(hours, results["wind_farm"], label="Wind")
axes[0].plot(hours, results["natural_gas_plant"], label="Gas")
axes[0].set_ylabel("MW")
axes[0].set_title("Generation dispatch")
axes[0].legend()

# --- Bottom plot: Availability profiles ---
axes[1].plot(hours, solar_output, label="Solar p.u.")
axes[1].plot(hours, wind_output, label="Wind p.u.")
axes[1].set_ylabel("p.u.")
axes[1].set_title("Availability profiles")
axes[1].legend()

plt.tight_layout()
plt.show()

