import pypsa as ps
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

original_network = ps.Network()

#setting up 1 year time series for the network
snapshots = pd.date_range("2024-01-01 00:00:00", "2024-12-31 23:00:00", freq="h")

original_network.set_snapshots(snapshots)

#adding the central bus
original_network.add("Bus", "Central_Bus", carrier="AC")

original_network.add("Generator", "Coal Plant", #coal base load  
                    bus="Central_Bus", 
                    p_nom=200, 
                    marginal_cost=40, 
                    carrier="coal")

original_network.add("Generator", "Gas Plant", #gas peaker plant. dispatched when demand exceed 200 (coal plant capacity)
                    bus="Central_Bus",
                    p_nom=150,
                    marginal_cost=70,
                    carrier="gas",
                    )

hourly_demand = np.random.randint(100, 320, len(snapshots)) #dummy demand profile for network

original_network.add("Load", "Demand", bus="Central_Bus", p_set=hourly_demand)

original_network.optimize()
print(f"Total cost: {original_network.objective} USD")
print(f"Total generation: {original_network.generators_t.p.sum()} MW")
print(f"Total demand: {original_network.loads_t.p_set.sum()} MW")
print(f"Total supply: {original_network.generators_t.p.sum()} MW")


gen_total = original_network.generators_t.p.sum(axis=1)
gen_daily = gen_total.resample("D").mean()
demand_daily = pd.Series(hourly_demand, index=snapshots).resample("D").mean()
price_daily = original_network.buses_t.marginal_price["Central_Bus"].resample("D").mean()

fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

 #Generation dispatct
axes[0].plot(gen_daily.index, demand_daily, label="Demand") #match perfectly so kind of pointless to plot on the same graph
axes[0].plot(gen_daily.index, gen_daily, label="Generation") 
axes[0].set_ylabel("MW")
axes[0].set_title("Daily average generation dispatch")
axes[0].legend()

# daily average Price per MWh in usd 
axes[1].plot(price_daily.index, price_daily, label="Price")
axes[1].set_ylabel("USD$/MWh")
axes[1].set_title("Daily average price")
axes[1].legend()

plt.tight_layout()
plt.show()




