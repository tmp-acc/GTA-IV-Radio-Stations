import json
import os
import re
import subprocess
from subprocess import call
from tkinter.messagebox import NO

audiofile_ext = ".m4a"
trtack_kind = "track"
snd_kinds = [
    trtack_kind, "news", "adverts", "extratracks", "weather", "solo", 
    "id", "intro", "outro", "to_news", "to_ad", 
    "to_weather", "general", "time_afternoon", "time_evening", 
    "time_morning", "time_night"
]

def get_snd_kind(path, prefix = ""): 
    for i, kind in enumerate(snd_kinds):
        subpath = prefix + kind + "/"
        if path.startswith(subpath) :
            return i, path[len(subpath):]
    if path.find("/") < 0 :
        return snd_kinds.index(trtack_kind), path
    return None, None

# kind, station, name
def get_path_info(path):
    common_kind, common_filename = get_snd_kind(path, prefix = "common/")
    if common_kind is not None:
        return common_kind, "", common_filename
    else :
        stationLen = path.find("/")
        station = path[:stationLen]
        stationFilePath = path[stationLen + 1:]

        kind, filename = get_snd_kind(stationFilePath)

        if kind is not None :
            return kind, station, filename
    return None, None, None


def get_sound_info(name):
    command = "ffmpeg -i \"" + name + "\"" #  + " -af silencedetect=noise=0.2:d=0.3 -f null -"
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (std_out, std_err) = p.communicate()
    m = re.search("Duration: (\d\d):(\d\d):(\d*.\d*)+, start", std_err)
    h, m, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
    file_duration = h * 60 * 60 + m * 60 + s
    sound_duration = None
    # m = re.findall("silence_start: (-?\d*.\d*).+", std_err)
    # if m :
    #     last_silence_start = float(m[-1])
    #     m = re.findall("silence_end: (-?\d*.\d*).+", std_err)
    #     if m :
    #         print(m)
    #         last_silence_end = float(m[-1])
    #         if last_silence_end < last_silence_start :
    #             sound_duration = last_silence_start
    #     else :
    #         sound_duration = last_silence_start
    return file_duration, sound_duration

def gather_meta(rootDir) :
    res = {}
    stations = {}
    rootDirLen = len(rootDir)
    for root, dirs, files in os.walk(rootDir):
        for name in files:
            filePath = os.path.join(root, name).replace("\\", "/")
            if not filePath.endswith(audiofile_ext):
                continue
            path = filePath[rootDirLen:]
            kind, stationName, name = get_path_info(path)
            if kind is not None :
                kindDesc = snd_kinds[kind]
                # print(stationName, kindDesc, name, filePath)
                file_duration, sound_duration = get_sound_info(filePath)
                info = {"path": path, "duration": file_duration }
                if sound_duration :
                    info ["audibleDuration"] = sound_duration
                if stationName :
                    if stationName not in stations :
                        stations[stationName] = {kindDesc: [info]}
                    else :
                        if kindDesc not in stations[stationName] :
                            stations[stationName][kindDesc] = [info]
                        else :
                            stations[stationName][kindDesc].append(info)
                else :
                    if kindDesc not in res :
                        res[kindDesc] = [info]
                    else :
                        res[kindDesc].append(info)
            else: 
                print(stationName, name, filePath)

    res["stations"] = stations
    return res


def save_series(meta):
    fileGroups = {}
    fileGroups["fileGroups"] = []
    for group_name in meta:
        if group_name == "stations": 
            continue

        fileGroup = {}
        fileGroup["tag"] = group_name
        fileGroup["files"] = meta[group_name]
        fileGroups["fileGroups"].append(fileGroup)

    common = {}
    common["common"] = fileGroups

    with open("series.json", "w") as outfile:
        json.dump(common, outfile, indent=4, separators=(',', ': '))


def remove_path_prefix(meta, prefix): 
    for obj in meta:
        path = obj["path"]
        if path.startswith(prefix):
            obj["path"] = path[len(prefix):]
    return meta


def add_intro(tracks, intros):
    # print("intros: ", intros)
    # print("tracks: ", tracks)



    for track_index, track in enumerate(tracks):
        track_info_path_start = "intro/" + track["path"][:-len(audiofile_ext)] + "_"
        track_intros = [intro for intro in intros if intro["path"].startswith(track_info_path_start)]


        if track_intros: 
            attaches = {}
            attaches["files"] = track_intros
            track["attaches"] = attaches
            tracks[track_index] = track

    print(tracks)
    return tracks

def save_station(station, meta): 
    result = {}
    result["fileGroups"] = []
    result["tag"] = station

    info = {}
    info["title"] = station
    info["genre"] = station
    info["logo"] = station + ".png"
    info["dj"] = station

    result["info"] = info

    intro = []
    tracks = []
    for group_name in meta:
        if group_name == "intro":
            intro = remove_path_prefix(meta[group_name], prefix= station + "/")
        elif group_name == "track":
            tracks = remove_path_prefix(meta[group_name], prefix= station + "/")
        else:
            file_group = {}
            file_group["tag"] = group_name
            file_group["files"] = remove_path_prefix(meta[group_name], prefix= station + "/")
            result["fileGroups"].append(file_group)

    # if info:
    print("----")

    tracks_file_group = {}
    tracks_file_group["tag"] = "track"
    tracks_file_group["files"] = add_intro(tracks, intros= intro)
    result["fileGroups"].append(tracks_file_group)

    with open("station_" + station + ".json", "w") as outfile:
        json.dump(result, outfile, indent=4, separators=(',', ': '))


def save_stations(meta):
    stations = meta["stations"]
    for station in stations:
        save_station(station, stations[station])




def do_the_harlem_shake() :
    meta = gather_meta("./")
    save_series(meta)
    save_stations(meta)

do_the_harlem_shake()