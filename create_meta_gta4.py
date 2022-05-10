import json
import os
import re
import subprocess
from subprocess import call

SndNews = 0
SndAdverts = 1
SndExtratracks = 2
SndWeather = 3
SndSolo = 4
SndId = 5
SndIntro = 6
SndOutro = 7
SndToNews = 8
SndToAdverts = 9
SndToWeather = 10
SndGeneral = 11
SndTrack = 12
SndTimeAfternoon = 13
SndtimeEvening = 14
SndtimeMorning = 15
SndtimeNight = 16

KindDesc = [
    "news", "adverts", "extratracks", "weather", "solo", 
    "id", "intro", "outro", "to_news", "to_adverts", 
    "to_weather", "general", "track", "time_afternoon", "time_evening", 
    "time_morning", "time_night"
]


def parseStationFilePath(path) :
    if path.startswith("solo/") :
        return SndSolo, path[len("solo/"):]
    if path.startswith("id/") :
        return SndId, path[len("id/"):]
    if path.startswith("intro/") :
        return SndIntro, path[len("intro/"):]
    if path.startswith("outro/") :
        return SndOutro, path[len("outro/"):]
    if path.startswith("to_weather/to_weather") :
        return SndToNews, path[len('to_weather/'):]
    if path.startswith("to_news/to_news") :
        return SndToNews, path[len('to_news/'):]
    if path.startswith("to_ad/to_ad") :
        return SndToAdverts, path[len("to_ad/"):]
    if path.startswith("general/") :
        return SndGeneral, path[len("general/"):]
    if path.startswith("time_afternoon/") :
        return SndTimeAfternoon, path[len("time_afternoon/"):]
    if path.startswith("time_evening/") :
        return SndtimeEvening, path[len("time_evening/"):]
    if path.startswith("time_morning/") :
        return SndtimeMorning, path[len("time_morning/"):]
    if path.startswith("time_night/") :
        return SndtimeNight, path[len("time_night/"):]
    if path.find("/") < 0 :
        return SndTrack, path
    return None, None

# kind, station, name
def getPathInfo(path):
    if path.startswith("common/news/") :
        return SndNews, "", path[len("common/news/"):]
    elif path.startswith("common/adverts/") :
        return SndAdverts, "", path[len("common/adverts/"):]
    elif path.startswith("common/extratracks/") :
        return SndExtratracks, "", path[len("common/extratracks/"):]
    elif path.startswith("common/weather/") :
        return SndWeather, "", path[len("common/weather/"):]
    else :
        stationLen = path.find("/")
        station = path[:stationLen]
        stationFilePath = path[stationLen + 1:]

        kind, filename = parseStationFilePath(stationFilePath)

        if kind is not None :
            return kind, station, filename

    return None, None, None


def getSoundInfo(name):
    command = "ffmpeg -i \"" + name + "\"" + " -af silencedetect=noise=0.2:d=0.3 -f null -"
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (std_out, std_err) = p.communicate()
    m = re.search("Duration: (\d\d):(\d\d):(\d*.\d*)+, start", std_err)
    h, m, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
    file_duration = h * 60 * 60 + m * 60 + s
    sound_duration = None
    m = re.findall("silence_start: (-?\d*.\d*).+", std_err)
    if m :
        last_silence_start = float(m[-1])
        m = re.findall("silence_end: (-?\d*.\d*).+", std_err)
        if m :
            last_silence_end = float(m[-1])
            if last_silence_end < last_silence_start :
                sound_duration = last_silence_start
        else :
            sound_duration = last_silence_start
    return file_duration, sound_duration

def createMetaJson(rootDir) :
    res = {}
    stations = {}
    rootDirLen = len(rootDir)
    for root, dirs, files in os.walk(rootDir):
        for name in files:
            filePath = os.path.join(root, name).replace("\\", "/")
            if not filePath.endswith('.m4a'):
                continue
            path = filePath[rootDirLen:]
            kind, stationName, name = getPathInfo(path)
            if kind is not None :
                kindDesc = KindDesc[kind]
                print(stationName, kindDesc, name, filePath)
                file_duration, sound_duration = getSoundInfo(filePath)
                info = {"path": path, "file_duration": file_duration }
                if sound_duration :
                    info ["sound_duration"] = sound_duration
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

FFMPEG_NAME = 'ffmpeg'

# call([FFMPEG_NAME, "-i", RECORD_NAME, "-ss", str(from_pos), "-to", str(to_pos), "-c", "copy", "-y", CUT_NAME])



#ffmpeg -i audio_radio/separated/radio_06_country/you_took_all_the_ramblin_out.mp3 -af silencedetect=noise=0.4:d=0.3 -f null -


def foo() :
    meta = createMetaJson("./")
    with open("meta.json", "w") as outfile:
        json.dump(meta, outfile, indent=4, separators=(',', ': '))

    #print getSoundInfo("gta5.fm/Contents/radio_01_class_rock/intro/0x0b0c2142.mp3")
    # print getSoundInfo("gta5.fm/Contents/radio_06_country/convoy.mp3")



foo()