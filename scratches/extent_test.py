# %%
import cool_maps.plot as cplt
import matplotlib.pyplot as plt

# %%
# Yucatan
extent = [-90, -78, 18, 26]
fig, ax = cplt.create(extent)
plt.savefig('yucatan.png', facecolor='white')
plt.close()

# %%
# Leeward
extent = [-68.5, -61, 15, 19]
fig, ax = cplt.create(extent)
plt.savefig('leeward.png', facecolor='white')
plt.close()

# %%
# GOM
extent = [-99, -79, 18, 31]
fig, ax = cplt.create(extent)
plt.savefig('gulf_of_mexico.png', facecolor='white')
plt.close()

# %%
# SAB
extent = [-82, -64, 25, 36]
fig, ax = cplt.create(extent)
plt.savefig('south_atlantic_bight.png', facecolor='white')
plt.close()

# %%
# MAB
extent = [-77, -67, 35, 43]
fig, ax = cplt.create(extent)
plt.savefig('mid_atlantic_bight.png', facecolor='white')
plt.close()

# %%
# West Florida Shelf
extent = [-87.5, -80, 24, 30.5]
fig, ax = cplt.create(extent)
plt.savefig('west_florida_shelf.png', facecolor='white')
plt.close()

# %%
# Caribbean
extent = [-89, -58, 7, 23]
fig, ax = cplt.create(extent)
plt.savefig('caribbean.png', facecolor='white')
plt.close()

# %%
# Windward
extent = [-68.2, -56.4, 9.25, 19.75]
fig, ax = cplt.create(extent)
plt.savefig('windward.png', facecolor='white')
plt.close()

# %%
# Amazon
extent = [-70, -43, 0, 20]
fig, ax = cplt.create(extent)
plt.savefig('amazon.png', facecolor='white')
plt.close()

# %%
# Hurricane
extent = [-89, -12, 0, 20]
fig, ax = cplt.create(extent)
plt.savefig('hurricane.png', facecolor='white')
plt.close()

# %% 
# Tropical Western Atlantic
extent = [-70, -40.7, 0, 25]
fig, ax = cplt.create(extent)
plt.savefig('western_tropical_atlantic.png', facecolor='white')
plt.close()

# %% 
# Atlantic
extent = [-90, -15.5, 0, 50]
fig, ax = cplt.create(extent)
plt.savefig('atlantic.png', facecolor='white')
plt.close()
# %%
