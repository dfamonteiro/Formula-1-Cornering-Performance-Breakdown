import fastf1 as ff1
from matplotlib import pyplot as plt
import matplotlib as mpl
from timple.timedelta import strftimedelta
from fastf1 import plotting
import numpy as np
from data import CORNER_COLORS, CORNER_TYPES
from gen_data import get_team_fastest_laps, corner_type_performance, label_lap
from sys import argv

# Straight-line: Full throttle
# High:       >200kph
# Medium-High: 150-200kph
# Medium-Low:  100-150kph
# Low:        <100kph


ff1.Cache.enable_cache('cache')

def plot_team_quali_performance(session : ff1.core.Session, ax : mpl.axes.Axes):
    "Plots the best lap of each team as an horizontal bar plot"
    fastest_laps = get_team_fastest_laps(session)
    pole_lap = fastest_laps.pick_fastest()

    team_colors = list()
    for index, lap in fastest_laps.iterlaps():
        try:
            color = ff1.plotting.team_color(lap['Team'])
        except KeyError:
            color = "black"
        team_colors.append(color)

    ax.barh(fastest_laps.index, fastest_laps['LapTimeDelta'], color=team_colors, edgecolor='grey')
    ax.set_yticks(fastest_laps.index)
    ax.set_yticklabels(fastest_laps['Driver'])

    # show fastest at the top
    ax.invert_yaxis()

    # draw vertical lines behind the bars
    ax.set_axisbelow(True)
    ax.xaxis.grid(True, which='major', linestyle='--', color='black', zorder=-1000)

    lap_time_string = strftimedelta(pole_lap['LapTime'], '%m:%s.%ms')

    ax.set_title(f"{session.event['EventName']} {session.event.year} Qualifying\n"
                 f"Fastest Lap: {lap_time_string} ({pole_lap['Driver']})")

def plot_track_map(lap : ff1.core.Lap, ax : mpl.axes.Axes):
    "Plots a track map, coloured by corner type"
    ax.set_aspect('equal', adjustable='box')
    ax.axis('off')

    for i0 in range(len(lap.telemetry)):
        i1 = (i0 + 1) % len(lap.telemetry)

        row0 = lap.telemetry.iloc[i0]
        row1 = lap.telemetry.iloc[i1]

        corner_type = row0["CornerType"]
        color = CORNER_COLORS[corner_type]

        ax.plot([row0["X"], row1["X"]], [row0["Y"], row1["Y"]], color=color, linestyle='-', linewidth = 2)

def plot_speedtrace(lap : ff1.core.Lap, ax : mpl.axes.Axes, time : bool = False):
    "Plots the speed trace of the given lap"
    ax.set(xlabel = "Time (s)" if time else "Distance (m)", ylabel = "Speed (km/h)")

    ax.axhline(y = 100, color = 'grey', linestyle = '-') 
    ax.axhline(y = 150, color = 'grey', linestyle = '-') 
    ax.axhline(y = 200, color = 'grey', linestyle = '-') 

    for i0 in range(len(lap.telemetry) - 1):
        i1 = i0 + 1

        row0 = lap.telemetry.iloc[i0]
        row1 = lap.telemetry.iloc[i1]

        corner_type = row0["CornerType"]
        color = CORNER_COLORS[corner_type]

        ax.plot(
            [row0["Time"] / np.timedelta64(1, 's'), row1["Time"] / np.timedelta64(1, 's')] if time else [row0["Distance"], row1["Distance"]], 
            [row0["Speed"], row1["Speed"]], 
            color=color, 
            linestyle='-', 
            linewidth = 1
        )
        ax.plot(
            [row0["Time"] / np.timedelta64(1, 's'), row1["Time"] / np.timedelta64(1, 's')] if time else [row0["Distance"], row1["Distance"]], 
            [row0["Throttle"] / 2, row1["Throttle"] / 2], 
            color=color, 
            linestyle='-', 
            linewidth = 1
        )

def plot_time_per_type(lap : ff1.core.Lap, ax : mpl.axes.Axes):
    "Plots the time spent on each corner type, as an horizontal bar plot"
    corner_performance = corner_type_performance(lap)
    times = [
        corner_performance["LOW"]        ["Time"],
        corner_performance["MEDIUM-LOW"] ["Time"],
        corner_performance["MEDIUM-HIGH"]["Time"],
        corner_performance["HIGH"]       ["Time"],
        corner_performance["STRAIGHT"]   ["Time"],
    ]
    print(times)
    ax.barh([0, 1, 2, 3, 4], times, color=["dodgerblue", "green", "orange", "red", "black"], edgecolor='grey')
    ax.set_yticks([0, 1, 2, 3, 4])
    ax.set_yticklabels(CORNER_TYPES)
    ax.set(xlabel = "Time (s)")

def plot_performance_per_car(session : ff1.core.Session, ax : mpl.axes.Axes):
    "Plots a breakdown of the performance of every team by corner types, as a parallel coordinates plot"
    fastest_laps = get_team_fastest_laps(session)
    team_corner_performance = {}
    for i, lap in fastest_laps.iterlaps():
        driver = lap["Driver"]
        print(f"Processing {driver}...")
        team = lap["Team"]
        try:
            label_lap(session, lap)
        except ValueError:
            # No clue why this happens. Maybe a ff1 bug? Bad data? Both? Who knows
            continue
        corner_performance = corner_type_performance(lap)
        
        team_corner_performance[team] = {}
        for corner_type in corner_performance:
            team_corner_performance[team][corner_type] = corner_performance[corner_type]["Speed"]
    
    averages = {}
    for ct in CORNER_TYPES:
        speeds = [team_corner_performance[team][ct] for team in team_corner_performance]
        averages[ct] = sum(speeds)/len(speeds)
    
    for team in team_corner_performance:
        if team == 'Haas F1 Team':
            team_color = "black"
        else:
            try:
                team_color = ff1.plotting.team_color(team)
            except KeyError:
                team_color = "black"
        speeds = []

        for ct in CORNER_TYPES:
            speeds.append(team_corner_performance[team][ct] - averages[ct])

        ax.plot([0, 1, 2, 3, 4], speeds, color = team_color)
    
    ax.set_xticks([0, 1, 2, 3, 4])
    ax.set_xticklabels(CORNER_TYPES,rotation = 25, ha='right')
    for i in range(5):
        ax.axvline(x = i, color = 'grey', linestyle = '-')

def show_track_stats(session : ff1.core.Session):
    "Shows the qualifying stats for a given session as a 2x3 grid of plots"
    fig, axes = plt.subplots(2, 3, figsize=(12, 12))

    plot_team_quali_performance(session, axes[0][0])

    lap = session.laps.pick_fastest()
    label_lap(session, lap)

    plot_speedtrace         (lap, axes[0][1])
    plot_track_map          (lap, axes[1][1])
    plot_time_per_type      (lap, axes[1][0])
    plot_performance_per_car(session, axes[0][2])

    plt.show()

def show_season_performance(year : int):
    "Shows the qualifying stats for every qualifying session of a given F1 season"
    for i in range(1, 30):
        try:
            quali_session = ff1.get_session(year, i, 'Q')
            print(f"Loading {quali_session}")
            quali_session.load()
        except ValueError:
            break
        except ff1.core.DataNotLoadedError:
            break

        tyres_used = set(quali_session.laps["Compound"])

        if ('INTERMEDIATE' in tyres_used or 'WET' in tyres_used) and str(quali_session) not in {'2023 Season Round 10: British Grand Prix - Qualifying',}:
            print("Wet weather tyres were used. Skipping this event")
            continue

        show_track_stats(quali_session)

if __name__ == "__main__":
    if len(argv) == 3 and argv[2] == "all":
        show_season_performance(int(argv[1]))
    elif len(argv) == 3:
        year = int(argv[1])
        round_number = int(argv[2])

        quali_session = ff1.get_session(year, round_number, 'Q')
        print(f"Loading {quali_session}")
        quali_session.load()
        show_track_stats(quali_session)
    else:
        print("Usage:")
        print(f"  {argv[0]} year 'all'")
        print(f"  {argv[0]} year round_number")