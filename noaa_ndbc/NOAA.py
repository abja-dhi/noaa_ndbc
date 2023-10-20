"""
################################################################################,
# Created Date:    '2023-10-17'                                                #,
# Author(s) :      Seyed Abbas Jazaeri - <abja@dhigroup.com>                   #,
#                                                                              #,
# Encoding:        UTF-8                                                       #,
# Language:        Python                                                      #,
# ---------------------------------------------------------------------------- #,
# Description: Download NOAA historical standard meteorological data from      #,
# National Data Buoy Center (NDBC) data by station id                          #,
#                                                                              #,
# ---------------------------------------------------------------------------- #,
# Copyright (c) (2022) DHI Water & Environment, Inc.                           #,
################################################################################
"""
import pandas as pd
import numpy as np
from urllib.request import urlopen
import bs4
import requests
import mikeio
import re
import os
from pykml import parser
import fiona
from tqdm import tqdm
from mikecore.DfsFile import eumUnit, eumItem
from mikeio.eum import EUMType, ItemInfo

def set_items(df):
    items = []
    for c in df.columns:
        if c == "WD":
            itemInfo = ItemInfo("Wind Direction", EUMType.Wind_Direction, eumUnit.eumUdegree)
        elif c == "WS":
            itemInfo = ItemInfo("Wind Speed", EUMType.Wind_speed, eumUnit.eumUmeterPerSec)
        elif c == "Gust_Speed":
            itemInfo = ItemInfo("Gust Speed", EUMType.Wind_speed, eumUnit.eumUmeterPerSec)
        elif c == "Hm0":
            itemInfo = ItemInfo("Sig. Wave Height", EUMType.Significant_wave_height, eumUnit.eumUmeter)
        elif c == "Tp":
            itemInfo = ItemInfo("Tp", EUMType.Wave_period, eumUnit.eumUsec)
        elif c == "T01":
            itemInfo = ItemInfo("T01", EUMType.Wave_period, eumUnit.eumUsec)
        elif c == "MWD":
            itemInfo = ItemInfo("Mean Wave Dir.", EUMType.Wave_direction, eumUnit.eumUdegree)
        elif c == "Sea_Level_Pressure":
            itemInfo = ItemInfo("Sea Level Pressure", EUMType.Pressure, eumUnit.eumUhectoPascal)
        elif c == "Air_Temperature":
            itemInfo = ItemInfo("Air Temperature", EUMType.Temperature, eumUnit.eumUdegreeCelsius)
        elif c == "Sea_Surface_Temperature":
            itemInfo = ItemInfo("Sea Surface Temperature", EUMType.Temperature, eumUnit.eumUdegreeCelsius)
        elif c == "Dewpoint_Temperature":
            itemInfo = ItemInfo("Dewpoint Temperature", EUMType.Temperature, eumUnit.eumUdegreeCelsius)
        elif c == "Visibility":
            itemInfo = ItemInfo("Visibility", EUMType.Visibility, None)
        elif c == "Pressure_Tendency":
            itemInfo = ItemInfo("Pressure Tendency", EUMType.Pressure, eumUnit.eumUhectoPascal)
        elif c == "Water_Level":
            itemInfo = ItemInfo("Water Level", EUMType.Water_Level, eumUnit.eumUfeet)
        elif "Depth " in c:
            itemInfo = ItemInfo("Water Depth", EUMType.Water_Depth, eumUnit.eumUmeter)
        elif "Current Direction " in c:
            itemInfo = ItemInfo("Current Direction", EUMType.Current_Direction, eumUnit.eumUdegree)
        elif "Current Speed " in c:
            itemInfo = ItemInfo("Current Speed", EUMType.Current_Speed, eumUnit.eumUCentiMeterPerSecond)


        items.append(itemInfo)

    return items

def mkch(path):
    try:
        os.mkdir(path)
    except:
        pass
    os.chdir(path)

def define_var(variable):
    if variable == "Meteorological":
        return "stdmet", "h"
    elif variable == "Currents":
        return "adcp", "a"
    elif variable == "Wind":
        return "cwind", "c"
    print("Variable is not defined!")
    quit()
    
def check_data_availability(station_id, variable="Meteorological"):
    var, letter = define_var(variable)
    years = []
    url = "https://www.ndbc.noaa.gov/historical_data.shtml"
    page = urlopen(url)
    html_bytes = page.read()
    html = html_bytes.decode("utf-8")
    soup = bs4.BeautifulSoup(html, "lxml")
    lst = soup.find("a", {"id": var}).parent
    histfiles = lst.find("ul", {"class": "histfiles"})
    stations = histfiles.find_all("li")
    for elem in stations:
        if elem.text.split(" ")[0].split(":")[0] == str(station_id):
            years_ = elem.find_all("a")
            for year in years_:
                years.append(int(year.text))
    return years

def download_file(station_id, y, variable="Meteorological"):
    log = open("logs.txt", "a")
    
    var, letter = define_var(variable)

    fname = "{station} - {year} - {var}.csv"
    url_base = "https://www.ndbc.noaa.gov/view_text_file.php?filename={station}{letter}{year}.txt.gz&dir=data/historical/{var}/"
    
    f = fname.format(station=str(station_id), year=str(y), var=var)
    url = url_base.format(station=str(station_id).lower(), year=str(y), var=var, letter=letter)
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        log.write("Data for " + str(station_id) + " for " + str(y) + " is not availble!\n")
        return False
    
    
    mkch(str(station_id))
    with open(f, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)
            
    lines = open(f, "r").readlines()
    fid = open(f, "w")
    for l in lines:
        fid.write(re.sub("\s+", ",", l)[0:-1]+"\n")
    fid.close()
    log.close()
    return True

def save_dfs0(df, fname):
    items = set_items(df)
    df.to_dfs0(fname, items=items)

def download(station_ids=[], start=None, end=None, csv=True, dfs0=False, merge=False, shapefile=False, shp_fname="Stations.shp", X=None, Y=None, variable="Meteorological"):
    log = open("logs.txt", "w")
    var, letter = define_var(variable)
    if type(station_ids) != list:
        station_ids = [station_ids]
    mainStart = start
    mainEnd = end
    if X != None and Y != None:
        station_ids = find_stations_within_box(X, Y)
        print("The following stations are found within the specified box:")
        log.write("The following stations are found within the specified box:\n")
        print(station_ids)
    
    for station_id in station_ids:
        years = check_data_availability(station_id, variable=variable)
        if len(years) == 0:
            log.write("No data is available for " + str(station_id) + "\n")
            continue
        if mainStart != None:
            start = int(mainStart)
        if mainEnd != None:
            end = int(mainEnd)
        if mainStart == None or mainStart < years[0]:
            start = years[0]
            log.write("Start year is set to " + str(start) + "\n")
        if mainEnd == None or mainEnd > years[-1]:
            end = years[-1]
            log.write("End year is set to " + str(end) + "\n")
        
        if dfs0 == False:
            csv = True
            log.write("CSV option is enabled!\n")
        dfMerged = pd.DataFrame()
        
        
        fname = "{station} - {year} - {var}.csv"
        for y in tqdm(range(start, end+1), desc=str(station_id)):
            
            currd = os.getcwd()
            f = fname.format(station=str(station_id), year=str(y), var=var)
            code = download_file(station_id, y, variable)
            if code:
                modify_csv(f, variable=variable)
                df = pd.read_csv(f, index_col=0, parse_dates=True)
                if dfs0:
                    save_dfs0(df, f.replace(".csv", ".dfs0"))
                    log.write(f.replace(".csv", ".dfs0") + " is downloaded!\n")
                #print("Data for " + str(y) + " is downloaded as " + f)
                if csv == False:
                    os.remove(f)
                else:
                    log.write(f + " is downloaded!\n")
                if merge:
                    #if dfMerged == None:
                        #dfsMerged = mikeio.read(f.replace(".csv", ".dfs0"))
                    #    dfMerged = df
                    #else:
                    dfMerged = pd.concat([dfMerged, df])
                        #dfsMerged = mikeio.Dataset.concat([dfsMerged, mikeio.read(f.replace(".csv", ".dfs0"))])
                os.chdir(currd)
        if merge and len(dfMerged.index) > 0:
            mkch(str(station_id))
            dfMerged.sort_index(axis=0, inplace=True)
            dfMerged.to_dfs0(str(station_id) + "," + str(start) + "-" + str(end) + " - "+ var + ".dfs0")
            os.chdir(currd)
    if shapefile:
        create_shapefile(station_ids=station_ids, file_name=shp_fname)
        log.write("Shapefile created!\n")
    log.close()

def NOAA_items(variable):
    if variable == "Meteorological":
        items = {"YY": "year", "YYYY": "year", "#YY": "year",
                 "MM": "month",
                 "DD":"day",
                 "hh": "hour", 
                 "mm": "minute", 
                 "WD": "WD", "WDIR": "WD",
                 "WSPD": "WS", 
                 "GST": "Gust_Speed",
                 "WVHT": "Hm0",
                 "DPD": "Tp",
                 "APD": "T01",
                 "MWD": "MWD",
                 "PRES": "Sea_Level_Pressure","BAR": "Sea_Level_Pressure",
                 "ATMP": "Air_Temperature",
                 "WTMP": "Sea_Surface_Temperature",
                 "DEWP": "Dewpoint_Temperature",
                 "VIS": "Visibility",
                 "PTDY": "Pressure_Tendency",
                 "TIDE": "Water_Level"}
    elif variable == "Currents":
        items = {}
        for i in range(1, 21):
            items["DEP"+str(i).zfill(2)] = "Depth "+str(i).zfill(2)
            items["DIR"+str(i).zfill(2)] = "Current Direction "+str(i).zfill(2)
            items["SPD"+str(i).zfill(2)] = "Current Speed "+str(i).zfill(2)
        items["YY"] = "year"
        items["YYYY"] = "year"
        items["#YY"] = "year"
        items["MM"] = "month"
        items["DD"] = "day"
        items["hh"] = "hour"
        items["mm"] = "minute"
    
                 
    return items

def replace_nans(df, items):
    nans = {}
    for key in items:
        if key == "WD" or key == "MWD" or key == "Air_Temperature" or key == "Sea_Surface_Temperature" or key == "Dewpoint_Temperature":
            nans[key] = 999.0
        elif key == "WS" or key == "Gust_Speed" or key == "Hm0" or key == "Tp" or key == "T01" or key == "Visibility" or key == "Water_Level":
            nans[key] = 99.0
        elif key == "Sea_Level_Pressure":
            nans[key] = 9999.0
    
    for c in df.columns:   
        df[c].replace(nans[c], np.nan, inplace=True)
        df[c].replace("MM", np.nan, inplace=True)
    
    return df
    
def modify_csv(fname, variable="Meteorological"):
    f = open(fname, "r")
    l0 = f.readline()
    l1 = f.readline()
    l2 = f.readline()
    skiprows = [0]
    if "#" in l1:
        skiprows = [1]
    f.close()
    
    if variable == "Meteorological":
        if skiprows == [0]:
            skiprows = 0
        df = pd.read_csv(fname, skiprows=skiprows)
    
        items = NOAA_items(variable)
        for c in df.columns:
            df.rename(columns={c: items[c]}, inplace=True)
    elif variable == "Currents":
        cols = len(l2.split(","))
        if cols%3 == 1:
            items = ["year", "month", "day", "hour"]
            tmp = 4
        else:
            items = ["year", "month", "day", "hour", "minute"]
            tmp = 5
        for i in range(1, int((cols-tmp)/3)+1):
            items = items + ["Depth "+str(i).zfill(2)]
            items = items + ["Current Direction "+str(i).zfill(2)]
            items = items + ["Current Speed "+str(i).zfill(2)]
        df = pd.read_csv(fname, skiprows=len(skiprows)+1, header=None)
        df.columns = items
    
    if "minute" not in df.columns:
        df["minute"] = np.zeros(len(df["year"]))
    if df.year[0] < 1000:
        df.year = df.year + 1900
    index = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute']])
    df.index = index
    df.index.name = "Datetime"
    df.drop(["year", "month", "day", "hour", "minute"], axis=1, inplace=True)
    
    if type(items) == dict:
        df = replace_nans(df, items.values())
    else:
        for c in df.columns:
            df[c].replace("MM", np.nan, inplace=True)
        #df = replace_nans(df, items)
    df.to_csv(fname)

def download_map():
    url = "https://www.ndbc.noaa.gov/kml/marineobs_as_kml.php?sort=pgm"
    map = requests.get(url)
    open("map.kml", "wb").write(map.content)

def find_stations_within_box(X, Y):
    download_map()
    f = open("map.kml", 'r', encoding="utf-8")
    doc = parser.parse(f).getroot()
    station_ids = []
    for folder in doc.Document.Folder.Folder:
        if folder.name != "Ships":
            for station in folder.Placemark:
                lon = float(station.LookAt.longitude)
                lat = float(station.LookAt.latitude)
                if lon > X[0] and lon < X[1] and lat > Y[0] and lat < Y[1]:
                    station_ids.append(station.name)
    f.close()
    os.remove("map.kml")
    return station_ids

def get_station_info(station_ids):
    download_map()
    if type(station_ids) != list:
        station_ids = [station_ids]
    stations_str = [str(elem) for elem in station_ids]
    f = open("map.kml", 'r', encoding="utf-8")
    doc = parser.parse(f).getroot()
    lons = []
    lats = []
    for folder in doc.Document.Folder.Folder:
        if folder.name != "Ships":
            for station in folder.Placemark:
                if str(station.name) in stations_str:
                    lons.append(station.LookAt.longitude)
                    lats.append(station.LookAt.latitude)
    f.close()
    os.remove("map.kml")
    return lons, lats

def create_shapefile(station_ids, file_name="Stations.shp"):
    # define schema
    if ".shp" not in file_name:
        file_name = file_name + ".shp"
    folder_name = file_name.split(".")[0]
    mkch(folder_name)
    schema = { 'geometry':'Point', 'properties':[('Name','str')]}
    fiona.supported_drivers

    pointShp = fiona.open(file_name, mode='w', driver='ESRI Shapefile', schema = schema, crs = "EPSG:4326")
    lons, lats = get_station_info(station_ids)
    for i in range(len(station_ids)):
        rowDict = { 'geometry' : {'type':'Point', 'coordinates': (lons[i],lats[i])}, 'properties': {'Name' : str(station_ids[i])}}
        pointShp.write(rowDict)
    pointShp.close()

