import pandas as pd
import fastf1 as ff1
from typing import List
import datetime
from matplotlib import pyplot as plt
from timple.timedelta import strftimedelta
from fastf1 import plotting
import numpy as np
from data import CORNER_LABELS, CORNER_TYPES

def plot_performance_per_car(data, ax, title, ylabel = False):
    for i in range(5):
        ax.axvline(x = i, color = 'grey', linestyle = '-')

    df = data.groupby(["Team", "CornerType"]).sum(numeric_only = True)
    df = df.drop(columns=["SessionNumber"])
    df["Speed"] = df["Distance"] / df["Time"]
    df = df.reset_index()
    teams = set(df["Team"])

    for team in teams:
        if team == 'Haas F1 Team':
            team_color = "black"
        else:
            team_color = ff1.plotting.team_color(team)
        speeds = []

        for ct in CORNER_TYPES:
            speed = float(df[df["Team"] == team][df["CornerType"] == ct]["Speed"])
            average = df[df["CornerType"] == ct]["Speed"].mean()
            speeds.append((speed - average) * 100 / average)

        ax.plot([0, 1, 2, 3, 4], speeds, color = team_color, linewidth = 3)
    ax.set_title(title)
    ax.set_xticks([0, 1, 2, 3, 4])
    ax.set_xticklabels(CORNER_TYPES,rotation = 25, ha='right')
    if ylabel:
        ax.set(ylabel = "Car speed as a percentage delta from the average")

def performance_projections(data):
    df = data.groupby(["Team", "CornerType"]).sum(numeric_only = True)
    df = df.drop(columns=["SessionNumber"])
    df["Speed"] = df["Distance"] / df["Time"]
    df = df.reset_index()
    teams = set(df["Team"])
    speeds = {}
    for team in teams:
        speeds[team] = {}
        for ct in CORNER_TYPES:
            speed = float(df[df["Team"] == team][df["CornerType"] == ct]["Speed"])
            average = df[df["CornerType"] == ct]["Speed"].mean()
            speeds[team][ct] = speed/average
    
    speeds = pd.DataFrame(speeds).T
    
    # CHange the list values in the line below
    low, medium_low, medium_high, high, straight = [9.036, 18.265, 13.62, 6.41, 36.493]

    speeds["LapTime"] = low  / speeds["LOW"]         +\
                 medium_low  / speeds["MEDIUM-LOW"]  +\
                 medium_high / speeds["MEDIUM-HIGH"] +\
                 high        / speeds["HIGH"]        +\
                 straight    / speeds["STRAIGHT"]
    
    print(speeds.sort_values(by=["LapTime"]))

if __name__ == "__main__":
    data = pd.read_json("cornering_data.json")

    bad_aston_martin_row = data[data["CornerType"] == "MEDIUM-HIGH"][data["GPName"] == ' United States Grand Prix'][data["Team"] == "Aston Martin"]
    data = data.drop(bad_aston_martin_row.index)

    data = data.drop(columns=['Speed'])

    fig, axes = plt.subplots(1, 3, figsize=(12, 12))
    performance_projections(data[data["SessionNumber"] >=15])
    plot_performance_per_car(data[data["SessionNumber"] <  9],                             axes[0], "Bahrain-Canada", ylabel=True)
    plot_performance_per_car(data[data["SessionNumber"] >= 9][data["SessionNumber"] < 15], axes[1], "Austria-Italy")
    plot_performance_per_car(data[data["SessionNumber"] >=15],                             axes[2], "Singapore onwards")

    fig.suptitle('F1 CAR PERFORMANCE BREAKDOWN\nLow: <100km/h | Medium-low: 100-150km/h\nMedium-high: 150-200km/h | High: >200km/h', fontsize=16)
    plt.show()