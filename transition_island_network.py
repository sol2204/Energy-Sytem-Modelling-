import pandas as pd
import pypsa as ps
import matplotlib.pyplot as plt

network_old = ps.Network()

emission_factor = {
    "Coal Plant": 0.9,
    "Gas Plant": 0.4,
    "Solar Plant": 0.0,
    "Wind Plant": 0.0,
}

snapshots = pd.date_range("2024-01-01 00:00:00", "2024-01-01 23:00:00", freq="h")
network_old.set_snapshots(snapshots)

network_old.add("Bus", "Central_Bus", carrier="AC")

network_old.add("Generator", "Coal Plant",
                bus="Central_Bus",
                p_nom=200,
                marginal_cost=80,
                emission_factor=emission_factor["Coal Plant"],
                carrier="coal",)

network_old.add("Generator", "Gas Plant",
                bus="Central_Bus",
                p_nom=150,
                marginal_cost=70,
                emission_factor=emission_factor["Gas Plant"],
                carrier="gas",)

hourly_demand = [180, 170, 165, 160, 160, 165, 170, 180, 190, 200,
                 210, 220, 230, 240, 245, 250, 245, 240, 230, 220,
                 210, 200, 190, 185,]


network_old.add("Load", "Demand", bus="Central_Bus", p_set=hourly_demand)

print(network_old.buses.index)
print(network_old.generators[["bus"]])

network_old.optimize() #LOPF

network_new = ps.Network() #new network for transition

snaptshots = pd.date_range("2024-01-01 00:00:00", "2024-01-01 23:00:00", freq="h")
network_new.set_snapshots(snapshots)

network_new.add("Bus", "Central_Bus", carrier="AC", )

solar_availability = [0, 0, 0, 0, 0, 0, 0.1, 0.2, 0.4, 0.6, 0.8,
                      0.9, 1.0, 0.9, 0.8, 0.6, 0.4, 0.2, 0.1, 0,
                      0, 0, 0, 0]

wind_availability = [0.6, 0.7, 0.8, 0.6, 0.5, 0.4, 0.6, 0.7, 0.8,
                     0.7, 0.6, 0.5, 0.4, 0.5, 0.6, 0.7, 0.8, 0.7,
                     0.6, 0.5, 0.4, 0.5, 0.6, 0.7]


network_new.add("Generator", "Gas Plant",
                bus="Central_Bus",
                p_nom=150,
                marginal_cost=200,
                emission_factor=emission_factor["Gas Plant"],
                carrier="gas")

network_new.add("Generator", "Solar Plant",
                bus="Central_Bus",
                p_nom_extendable=True,
                capital_cost=600,
                p_max_pu=solar_availability,
                marginal_cost=0,
                emission_factor=emission_factor["Solar Plant"],
                carrier="solar")

network_new.add("Generator", "Wind Plant",
                bus="Central_Bus",
                p_nom_min=150, #Forcing the model to build exactly 150MW of wind power 
                p_nom_max=150, 
                capital_cost=700, #at a capex of 700 units
                p_nom_extendable=True,
                p_max_pu=wind_availability,
                marginal_cost=0,
                emission_factor=emission_factor["Wind Plant"],
                carrier="wind")

network_new.add("Load", "Demand", bus="Central_Bus", p_set=hourly_demand)


network_new.optimize() #LOPF
print(f"Total cost opex + capex: {network_new.objective} USD")
print(f"Total cost of old system: {network_old.objective} USD")
print(f"Time to pay off investment: {network_new.objective / network_old.objective:.2f} days")
print(f"optimized solar plant capacity: {network_new.generators.at['Solar Plant', 'p_nom_opt']:.2f} MW")

print(f"Difference in cost between old and new system: {network_new.objective - network_old.objective} USD")


def plot_dispatch_subplots(network_old, network_new, title=None):
    """
    Plot stacked generator dispatch for old and new networks
    in two vertically stacked subplots with shared axes.
    """

    # Generator dispatch
    p_old = network_old.generators_t.p
    p_new = network_new.generators_t.p

    # Carrier mapping
    carr_old = network_old.generators["carrier"]
    carr_new = network_new.generators["carrier"]

    # Aggregate by carrier
    old_by_carrier = p_old.groupby(carr_old, axis=1).sum()
    new_by_carrier = p_new.groupby(carr_new, axis=1).sum()


    # Plot
    fig, axes = plt.subplots(
        nrows=2,
        ncols=1,
        figsize=(12, 6),
        sharex=True,
        sharey=True
    )

    old_by_carrier.plot.area(ax=axes[0], linewidth=0)
    new_by_carrier.plot.area(ax=axes[1], linewidth=0)

    # old_by_carrier.plot(ax=axes[0], kind="bar", stacked=True)
    # new_by_carrier.plot(ax=axes[1],  kind="bar", stacked=True)
   
    axes[0].set_title("Old system")
    axes[1].set_title("New system")
    axes[1].set_xlabel("Time")
    axes[0].set_ylabel("Generation (MW)")
    axes[1].set_ylabel("Generation (MW)")

    if title:
        fig.suptitle(title, fontsize=14)

    for ax in axes:
        ax.grid(True, alpha=0.3)

    axes[0].legend(loc="upper left")

    plt.tight_layout()
    plt.show()

plot_dispatch_subplots(
    network_old,
    network_new,
    title="Generation dispatch: old vs new system"
)

#function to calculate total emissions from the network
def calculate_total_emissions(network):
    emissions = 0 
    for generator, generator_data in network.generators.iterrows():
        generation = network.generators_t.p[generator]
        emissions_factor = generator_data["emission_factor"]
        gen_emissions = sum(generation * emissions_factor)
        emissions += gen_emissions
    return emissions

old_emissions = calculate_total_emissions(network_old)
print(f"Total emissions from old system: {old_emissions} kgCO2")
new_emissions = calculate_total_emissions(network_new)
print(f"Total emissions from new system: {new_emissions} kgCO2")
print(f"Percentage reduction in emissions: {(old_emissions - new_emissions) / old_emissions * 100:.2f}%")