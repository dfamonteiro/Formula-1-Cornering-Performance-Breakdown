import pandas as pd
import fastf1 as ff1
from typing import List
from matplotlib import pyplot as plt
import matplotlib
from fastf1 import plotting
from data import CORNER_TYPES

BAD_DATA = [
   (' United States Grand Prix', "Aston Martin", "MEDIUM-HIGH"),
   (' Las Vegas Grand Prix', "McLaren")
]

def plot_performance(data : pd.DataFrame, ax : matplotlib.axis.Axis, title : str, ylabel : bool = False):
    """Plots a breakdown of the performance of the car by corner types, as a parallel coordinates plot

    Args:
        data (pd.DataFrame): The performance data to be processed and displayed
        ax (matplotlib.axis.Axis): The "canvas" for the plot
        title (str): Title of the plot
        ylabel (bool, optional): Decide whether to show the y label. Defaults to False.
    """
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

def project_pecking_order(data : pd.DataFrame, track_corners : List[float]):
    """Prints a projected pecking order based on past cornering performance data and a set of track characteristics

    Args:
        data (pd.DataFrame): Past cornering performance data
        track_corners (List[float]): List of 5 floats, that represent the following parameters:
            - time spent on low-speed corners
            - time spent on medium_low-speed corners
            - time spent on medium_high-speed corners
            - time spent on high-speed corners
            - time spent on straights
    """
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
    
    # Change the list values in the line below
    low, medium_low, medium_high, high, straight = track_corners

    speeds["LapTime"] = low  / speeds["LOW"]         +\
                 medium_low  / speeds["MEDIUM-LOW"]  +\
                 medium_high / speeds["MEDIUM-HIGH"] +\
                 high        / speeds["HIGH"]        +\
                 straight    / speeds["STRAIGHT"]
    
    print(speeds.sort_values(by=["LapTime"]))

if __name__ == "__main__":
    data = pd.read_json("cornering_data.json")

    # First: delete the bad rows
    for row in BAD_DATA:
        if len(row) == 2:
            gp, team = row
            bad_data = data[data["GPName"] == gp][data["Team"] == team]
        elif len(row) == 3:
            gp, team, corner_type = row
            bad_data = data[data["GPName"] == gp][data["Team"] == team][data["CornerType"] == corner_type]
        data = data.drop(bad_data.index)
    data = data.drop(columns=['Speed'])

    # Second: replace the deleted rows with averaged values
    for row in BAD_DATA:
        if len(row) == 2:
            gp, team = row
            for corner_type in CORNER_TYPES:
                cornering_data = data[data["GPName"] == gp][data["CornerType"] == corner_type]
                mean_distance = cornering_data["Distance"].mean()
                mean_time = cornering_data["Time"].mean()
                session_number = int(cornering_data["SessionNumber"].median())
                averaged_entry = {
                    "Distance" : mean_distance,
                    "Time" : mean_time,
                    "CornerType" : corner_type,
                    "Team" : team,
                    "GPName" : gp,
                    "SessionNumber" : session_number,
                }
                data = pd.concat([data, pd.DataFrame([averaged_entry])], ignore_index=True)
        elif len(row) == 3:
            gp, team, corner_type = row
            cornering_data = data[data["GPName"] == gp][data["CornerType"] == corner_type]
            mean_distance = cornering_data["Distance"].mean()
            mean_time = cornering_data["Time"].mean()
            session_number = int(cornering_data["SessionNumber"].median())
            averaged_entry = {
                "Distance" : mean_distance,
                "Time" : mean_time,
                "CornerType" : corner_type,
                "Team" : team,
                "GPName" : gp,
                "SessionNumber" : session_number,
            }
            data = pd.concat([data, pd.DataFrame([averaged_entry])], ignore_index=True)

    fig, axes = plt.subplots(1, 3, figsize=(12, 12))
    plot_performance(data[data["SessionNumber"] <  9],                             axes[0], "Bahrain-Canada", ylabel=True)
    plot_performance(data[data["SessionNumber"] >= 9][data["SessionNumber"] < 15], axes[1], "Austria-Italy")
    plot_performance(data[data["SessionNumber"] >=15],                             axes[2], "Singapore onwards")

    fig.suptitle('F1 CAR PERFORMANCE BREAKDOWN\nLow: <100km/h | Medium-low: 100-150km/h\nMedium-high: 150-200km/h | High: >200km/h', fontsize=16)
    plt.show()