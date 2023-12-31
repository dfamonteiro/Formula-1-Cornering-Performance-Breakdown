import fastf1 as ff1
from typing import List
import datetime
from matplotlib import pyplot as plt
import pandas as pd
from timple.timedelta import strftimedelta
from fastf1 import plotting
import numpy as np
from data import CORNER_LABELS, CORNER_COLORS, CORNER_TYPES

# Straight-line: Full throttle
# High:       >200kph
# Medium-High: 150-200kph
# Medium-Low:  100-150kph
# Low:        <100kph


ff1.Cache.enable_cache('cache')

def get_team_fastest_laps(session : ff1.core.Session) -> ff1.core.Laps:
    teams = pd.unique(session.laps['Team'])
    list_fastest_laps = list()
    for team in teams:
        fastest_team_lap       = session.laps.pick_team(team).pick_fastest(only_by_time=True)
        fastest_legal_team_lap = session.laps.pick_team(team).pick_fastest()
        fastest_team_lap["LegalLapTime"] = fastest_legal_team_lap
        list_fastest_laps.append(fastest_team_lap)

    fastest_laps = ff1.core.Laps(list_fastest_laps, session = session).sort_values(by='LapTime').reset_index(drop=True)
    pole_lap = fastest_laps.pick_fastest(only_by_time=True)
    fastest_laps['LapTimeDelta'] = fastest_laps['LapTime'] - pole_lap['LapTime']

    return fastest_laps

def plot_team_quali_performance(session : ff1.core.Session, ax):
    fastest_laps = get_team_fastest_laps(session)
    pole_lap = fastest_laps.pick_fastest()

    team_colors = list()
    for index, lap in fastest_laps.iterlaps():
        color = ff1.plotting.team_color(lap['Team'])
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

def plot_track_map(lap, ax):
    ax.set_aspect('equal', adjustable='box')
    ax.axis('off')

    for i0 in range(len(lap.telemetry)):
        i1 = (i0 + 1) % len(lap.telemetry)

        row0 = lap.telemetry.iloc[i0]
        row1 = lap.telemetry.iloc[i1]

        corner_type = row0["CornerType"]
        color = CORNER_COLORS[corner_type]

        ax.plot([row0["X"], row1["X"]], [row0["Y"], row1["Y"]], color=color, linestyle='-', linewidth = 2)

def plot_speedtrace(lap, ax, time = False):
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

def corner_type_performance(lap):
    segments = [
        ("STRAIGHT", 0, 0)
    ]

    for i0 in range(len(lap.telemetry) - 1):
        i1 = i0 + 1

        row0 = lap.telemetry.iloc[i0]
        row1 = lap.telemetry.iloc[i1]

        if row0["CornerType"] != row1["CornerType"]:
            segments.append(
                (row1["CornerType"], row0["Distance"], row0["Time"] / np.timedelta64(1, 's'))
            )
    
    last_row = lap.telemetry.iloc[-1]
    segments.append(
        (last_row["CornerType"], last_row["Distance"], last_row["Time"] / np.timedelta64(1, 's'))
    )

    res = {
        'STRAIGHT'    : {"Distance" : 0, "Time" : 0},
        'LOW'         : {"Distance" : 0, "Time" : 0},
        'MEDIUM-LOW'  : {"Distance" : 0, "Time" : 0},
        'MEDIUM-HIGH' : {"Distance" : 0, "Time" : 0},
        'HIGH'        : {"Distance" : 0, "Time" : 0},
    }

    for i in range(len(segments) - 1):
        d = segments[i + 1][1] - segments[i][1]
        t = segments[i + 1][2] - segments[i][2]
        corner_type = segments[i][0]
        
        cd, ct = res[corner_type]["Distance"], res[corner_type]["Time"]
        cd += d
        ct += t

        res[corner_type] = {"Distance" : cd, "Time" : ct}
    
    for key in res:
        res[key]["Speed"] = res[key]["Distance"] / res[key]["Time"] if (res[key]["Time"] > 0) else 0

    return res

def plot_time_per_type(lap, ax):
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

def plot_performance_per_car(session, ax):
    fastest_laps = get_team_fastest_laps(session)
    team_corner_performance = {}
    for i, lap in fastest_laps.iterlaps():
        driver = lap["Driver"]
        print(f"Processing {driver}...")
        team = lap["Team"]
        label_lap(session, lap)
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
            team_color = ff1.plotting.team_color(team)
        speeds = []

        for ct in CORNER_TYPES:
            speeds.append(team_corner_performance[team][ct] - averages[ct])

        ax.plot([0, 1, 2, 3, 4], speeds, color = team_color)
    
    ax.set_xticks([0, 1, 2, 3, 4])
    ax.set_xticklabels(CORNER_TYPES,rotation = 25, ha='right')
    for i in range(5):
        ax.axvline(x = i, color = 'grey', linestyle = '-')

def label_lap(session, lap):
    corner_type = []
    for index, row in lap.telemetry.iterrows():
        for t, start, finish in CORNER_LABELS[str(session)]:
            if start < row["Distance"] <= finish:
                corner_type.append(t)
                break
        else:
            corner_type.append("STRAIGHT")
    
    lap.telemetry["CornerType"] = corner_type

def show_track_characteristics(session : ff1.core.Session):
    fig, axes = plt.subplots(2, 3, figsize=(12, 12))

    plot_team_quali_performance(session, axes[0][0])

    lap = session.laps.pick_fastest()
    label_lap(session, lap)

    plot_speedtrace         (lap, axes[0][1])
    plot_track_map          (lap, axes[1][1])
    plot_time_per_type      (lap, axes[1][0])
    plot_performance_per_car(session, axes[0][2])

    plt.show()

def show_season_performance():
    for i in range(1, 30):
        try:
            quali_session = ff1.get_session(2023, i, 'Q')
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

        show_track_characteristics(quali_session)

def gen_cornering_performance_data():
    data = []
    for i in range(1, 30):
        try:
            quali_session = ff1.get_session(2023, i, 'Q')
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

        ##########################################################################
        fastest_laps = get_team_fastest_laps(quali_session)
        
        for _, lap in fastest_laps.iterlaps():
            driver = lap["Driver"]
            print(f"Processing {driver}...")
            team = lap["Team"]
            label_lap(quali_session, lap)
            corner_performance = corner_type_performance(lap)
            
            for key in corner_performance:
                entry = corner_performance[key]
                entry["CornerType"] = key
                entry["Team"] = team
                entry["GPName"] = str(quali_session)[21:-13]
                entry["SessionNumber"] = i
                
                data.append(entry)
        
    data = pd.DataFrame(data)
    data.to_json("cornering_data.json")


if __name__ == "__main__":
    gen_cornering_performance_data()
    show_season_performance()

    #########################################
    # quali_session = ff1.get_session(2023, 22, 'Q')
    # print(f"Loading {quali_session}")
    # quali_session.load()
    # show_track_characteristics(quali_session)
    #########################################