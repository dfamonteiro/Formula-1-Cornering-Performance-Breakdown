from sys import argv
import fastf1 as ff1
from typing import Set, List
from gen_data import label_lap, corner_type_performance
import pandas as pd
from sklearn.cluster import KMeans
from matplotlib import pyplot as plt

ff1.Cache.enable_cache('cache')

def get_season_quali_sessions(year : int, override : Set[str] = set()) -> List[ff1.core.Session]:
    "Get the dry qualifying sessions from an F1 season"
    res = []
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

        if ('INTERMEDIATE' in tyres_used or 'WET' in tyres_used) and str(quali_session) not in override:            
            print("Wet weather tyres were used. Skipping this event")
            continue
        res.append(quali_session)

    return res

def get_gp_name(full_name : str) -> str:
    gp_start = full_name.index(":") + 2
    gp_end = full_name.index(" - Qualifying")
    res = full_name[gp_start:gp_end]
    res = res.replace("Grand Prix", "GP")

    return res


def get_track_corners_breakdown(sessions : List[ff1.core.Session]) -> pd.DataFrame:
    res = {}

    for session in sessions:
        gp_name = get_gp_name(str(session))

        print(f"Processing {gp_name}...")
        lap = session.laps.pick_fastest()
        label_lap(session, lap)
        corner_performance = corner_type_performance(lap)
        for corner_type in corner_performance:
            corner_performance[corner_type] = round(corner_performance[corner_type]["Time"], 4)
        res[gp_name] = corner_performance
    
    return pd.DataFrame(res).T

def check_for_every_race(dt : pd.DataFrame):
    f1_2024 = {"Bahrain", "Saudi Arabian", "Australian", "Japanese", "Chinese", "Miami",
                "Emilia Romagna", "Monaco", "Canadian", "Spanish", "Austrian", "British",
                "Hungarian", "Belgian", "Dutch", "Italian", "Azerbaijan", "Singapore", "United States",
                "Mexico City", "São Paulo", "Las Vegas", "Qatar", "Abu Dhabi"}
    f1_2024 = set(place + " GP" for place in f1_2024)

    differences = f1_2024.difference(set(dt.index)).union(set(dt.index).difference(f1_2024))

    if len(differences) > 0:
        print(sorted(differences))
        exit()

def gen_data():
    sessions = get_season_quali_sessions(2023, {'2023 Season Round 10: British Grand Prix - Qualifying',})

    missing_session_keys = ((2019, 3), (2022, 15), (2022, 14), (2019, 7), (2021, 2))
    for year, race in missing_session_keys:
        session = ff1.get_session(year, race, 'Q')
        print(f"Loading {get_gp_name(str(session))}")
        session.load()
        sessions.append(session)
        # print(set(session.laps["Compound"]))

    dt = get_track_corners_breakdown(sessions)
    print(dt)
    dt.to_json("track_corners_db.json")

def elbow_method(dt : pd.DataFrame):
    # https://www.w3schools.com/python/python_ml_k-means.asp
    inertias = []

    for i in range(1,11):
        kmeans = KMeans(n_clusters=i, n_init=10)
        kmeans.fit(dt)
        inertias.append(kmeans.inertia_)

    plt.plot(range(1,11), inertias, marker='o')
    plt.title('Elbow method')
    plt.xlabel('Number of clusters')
    plt.ylabel('Inertia')
    plt.show() 

def kmeans_clustering(dt : pd.DataFrame, n : int = 2):
    kmeans = KMeans(n_clusters=n, n_init='auto')
    kmeans.fit(dt)

    dt1 = dt.copy(True)

    dt1["Cluster"] = kmeans.labels_
    
    res = {}
    for i in range(n):
        gp_cluster = dt1[dt1["Cluster"] == i]
        print(gp_cluster)
        print(list(gp_cluster.index))
        print()
        res[i] = (gp_cluster, list(gp_cluster.index))
    
    return res

def normalize(dt : pd.DataFrame) -> pd.DataFrame:
    res = dt.copy(True)
    res["Total"] = res["STRAIGHT"] + res["LOW"] + res["MEDIUM-LOW"] + res["MEDIUM-HIGH"] + res["HIGH"]
    for c in ("STRAIGHT", "LOW", "MEDIUM-LOW", "MEDIUM-HIGH", "HIGH"):
        res[c] = res[c] * 100 / res["Total"]
    res = res.drop(["Total"], axis=1)
    return res

if __name__ == "__main__":
    if len(argv) == 1:
        print("Usage:")
        print(f"  {argv[0]} gen | generate 'track_corners_db.json'")
        print(f"  {argv[0]} run | runs the K-means clustering method on the 'track_corners_db.json' data")
    elif len(argv) == 2 and argv[1] == "gen":
        gen_data()
    elif len(argv) == 2 and argv[1] == "run":
        dt = pd.read_json("track_corners_db.json")
        df = normalize(dt)

        elbow_method(df)
        for i in (2, 3, 4):
            kmeans_clustering(df, i)
            print("="*80)
    elif len(argv) == 2:
        print("Invalid argument")
    else:
        print("Too many arguments")
    