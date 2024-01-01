import fastf1 as ff1
import pandas as pd
import numpy as np
from data import CORNER_LABELS
from typing import Set, Dict

# Straight-line: Full throttle
# High:       >200kph
# Medium-High: 150-200kph
# Medium-Low:  100-150kph
# Low:        <100kph

ff1.Cache.enable_cache('cache')

def corner_type_performance(lap : ff1.core.Lap) -> Dict[str, Dict[str, float]]:
    "Outputs the time, distance and speed spent on each type of corner for any given labelled lap."
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

def get_team_fastest_laps(session : ff1.core.Session) -> ff1.core.Laps:
    "Get the fastest lap (illegal or not) of every team in the session."
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

def label_lap(session : ff1.core.Session, lap : ff1.core.Lap):
    "Assign a corner type for every datapoint in the lap."
    corner_type = []
    for index, row in lap.telemetry.iterrows():
        for t, start, finish in CORNER_LABELS[str(session)]:
            if start < row["Distance"] <= finish:
                corner_type.append(t)
                break
        else:
            corner_type.append("STRAIGHT")
    
    lap.telemetry["CornerType"] = corner_type

def gen_cornering_performance_data(year : int, path : str, force_include : Set[str] = {}):
    "Generates cornering performance data for car and track in the season."
    data = []
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

        if ('INTERMEDIATE' in tyres_used or 'WET' in tyres_used) and str(quali_session) not in force_include:
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
    data.to_json(path)

if __name__ == "__main__":
    gen_cornering_performance_data(2023, "cornering_data.json", {'2023 Season Round 10: British Grand Prix - Qualifying',})
