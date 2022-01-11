#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 11 15:52:17 2022

@author: sylvain
"""

import numpy as np
from calendar import monthrange
import pandas as pd



# Hypotheses
eta_pp = 0.7      # Average efficiency of the plunger pumps
eta_surpr = 0.4   # average efficiency of the "surpresseur" pumps
C_day = 250       # average daily water consumption in m³
depth = 70        # Depth of the wells
p_nom = 5e5       # nominal absolute pressure of the water distribution
V_dot_nom = C_day/10   # nominal flow rate of the pumps in m³/h 
n_days=150            # number of days in the year where the 250m³ are needed


# Average daily consumption:
C_joules = 1000 * 9.81 * depth * C_day / eta_pp + C_day * (p_nom - 1E5)/eta_surpr
# in kWh:
C_kwh = C_joules/3.6e6
print('daily electricity consumption for water pumping:' + str(C_kwh) + ' kWh')
print('monthly electricity consumption for water pumping:' + str(30*C_kwh) + ' kWh')
print('yearly electricity consumption for water pumping:' + str(150*C_kwh) + ' kWh')

# Nominal electricity consumption of the pumps:
V_dot_nom_m3s = V_dot_nom/3600
W_dot_nom = (1000 * 9.81 * depth * V_dot_nom_m3s / eta_pp + V_dot_nom_m3s * (p_nom - 1E5)/eta_pp )/1000
print('Nominal power of the pumps: ' + str(W_dot_nom) + ' kW')

# Ratio between water consumption and electricity consumption:
water_elec_cost = C_kwh/C_day
print('Specific electricity of water: ' + str(water_elec_cost) + ' kWh/m³')


daily_profiles = pd.read_csv('PV_casamance - daily profiles.csv',index_col=0)
daily_profiles.plot()

profile = pd.DataFrame(index=pd.date_range(start='2015-01-01 00:00',end='2015-12-31 23:59',freq='1h'))
water = pd.Series(index=pd.date_range(start='2015-01-01 00:00',end='2015-12-31 23:59',freq='1h'))
conso = pd.Series(index=range(1,13),data=[8580, 10316, 7429, 16165, 10114, 5089, 2851, 2108, 2138, 3463, 6492, 8500])

profile['Lighting and others'] = 0
profile['Plunger Pump'] = 0
profile['Plunger Pump day'] = 0
profile['Surpresseurs'] = 0

profile_flat = profile

conso_base = 2100

for m in range(1,13):
    n_days = monthrange(2015, m)[1]
    conso_pp = conso[m] - conso_base
    idx_month = (profile.index.month == m)
    conso_w_month = conso_pp/water_elec_cost
    print('Water consumption for month ' + str(m) + ': ' + str(conso_w_month) + ' m³')
    conso_w_day = conso_w_month/n_days
    n_hours_pumping = conso_w_day/V_dot_nom
    conso_left = conso_w_day
    daily_cons = np.zeros(24)
    hh = 0
    while conso_left>0:
        if conso_left > 2 * V_dot_nom:
            daily_cons[-hh] = V_dot_nom
            daily_cons[1+hh] = V_dot_nom
            conso_left -= 2 * V_dot_nom
        else:
            daily_cons[-hh] = conso_left/2
            daily_cons[1+hh] = conso_left/2
            conso_left = 0
        hh += 1      
    
    # loop through each day
    for n in range(1,n_days+1):
        idx = (profile.index.month == m) & (profile.index.day==n)
        profile.loc[idx,'Lighting and others'] = daily_profiles['Lighting & other'].values
        if m<6 or m >10: 
            water[idx] = daily_profiles['Water cons wet season'].values
        else:
            water[idx] = daily_profiles['Water cons dry season'].values
            
        profile.loc[idx,'Plunger Pump'] = daily_cons * 1000 * 9.81 * depth / eta_pp / 3.6E6
        profile.loc[idx,'Plunger Pump day'] = daily_cons[range(-12,12)] * 1000 * 9.81 * depth / eta_pp / 3.6E6

    water[idx_month] =  water[idx_month] * conso_w_month/water[idx_month].sum()
    profile.loc[idx_month,'Surpresseurs'] = water[idx_month].values * (p_nom - 1E5)/eta_surpr/3.6E6
    profile.loc[idx_month,'Lighting and others'] =  profile.loc[idx_month,'Lighting and others'] * conso_base/profile.loc[idx_month,'Lighting and others'].sum()
    
demand_night = profile['Lighting and others'] + profile['Plunger Pump'] + profile['Surpresseurs']
demand_day = profile['Lighting and others'] + profile['Plunger Pump day'] + profile['Surpresseurs']

profile.to_csv('PV_casamance - yearly profiles.csv')



