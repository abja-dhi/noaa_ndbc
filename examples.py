from noaa_ndbc import NOAA
"""
#NOAA.download input argument definitions:
#station_ids (int, str, list of int and str):
#   default: []
#   Single station ID or a list of station IDs

# start (int)
#   default: None
#   The first year of the required data to be downloaded. It will be changed to the first available year in case it is after the specified year

# end (int)
#   default: None
#   The last year of the required data to be downloaded. It will be changed to the last available year in case it is before the specified year

# csv (True or False)
#   default: True
#   Print downloaded data to a csv file or not. In case that all formats are set to False, csv would be enabled

# dfs0 (True or False)
#   default: False
#   Print downloaded data to a dfs0 file or not

# merge (True or False)
#   default: False
#   Merge downloaded data to a single dfs0 file or not

# shapefile (True or False)
#   default: False
#   Prepare a point shapefile including all the processed stations

# shp_fname (str)
#   default: "Stations.shp"
#   The shapefile name in case Shapefile is set to True

#### The module is able to search for the available stations within a specified bounding box.
#### The coordinates of the bounding box are defined using X and Y variables
# X ([float, float])
#   default: None
#   A 2-element list of minimum and maximum X values for the bounding box
# Y ([float float])
#   default: None
#   A 2-element list of minimum and maximum Y values for the bounding box

# variable ("Meteorological" or "Currents")
#   default: "Meteorological"
#   The type of variables to be downloaded for the stations
"""
#Download data for a single station in CSV format
NOAA.download(46022)
NOAA.download("46022")
#Download data for a group of stations in CSV format
NOAA.download([46022, "HBXC1"], variable="Meteorological")
#Download data for a group of stations in CSV format starting 1995 (The start date will be replaced with the first available year in case it is after the specified year)
NOAA.download([46022, "HBXC1"], start=1995, variable="Currents")
#Download data for a group of stations in CSV format ending at 1995 (The end date will be replaced with the last available year in case it is before the specified year)
NOAA.download([46022, "HBXC1"], end=2010)
#Download data for a group of stations in CSV format within the specified range
NOAA.download([46022, "HBXC1"], start=1995, end=2010)
#Download data in both CSV and dfs0 formats
NOAA.download([46022, "HBXC1"], dfs0=True)
#Download data only in dfs0 format
NOAA.download([46022, "HBXC1"], dfs0=True, csv=False)
#Download data and export the location of the stations as a shapefile with the name "Stations.shp"
NOAA.download([46022, "HBXC1"], dfs0=True, csv=False, shapefile=True)
#Download data and export the location of the stations as a shapefile with the specified name
NOAA.download([46022, "HBXC1"], dfs0=True, csv=False, shapefile=True, shp_fname="Test1")
NOAA.download([46022, "HBXC1"], dfs0=True, csv=False, shapefile=True, shp_fname="Test2.shp")
#######
#Download data for all the stations within the specified bounding box
#######
NOAA.download(X=[-127, -124], Y=[40, 42])
NOAA.download(X=[-127, -124], Y=[40, 42], dfs0=True)
NOAA.download(X=[-127, -124], Y=[40, 42], dfs0=True, csv=False, shapefile=True, shp_fname="Test3")


#Other utilities
#Check the availability of the data for a single station
years = NOAA.check_data_availability(46022, variable="Meteorological")
print(years)

#Get the station IDs within a bounding box
station_ids = NOAA.find_stations_within_box(X=[-127, -124], Y=[40, 42])
print(station_ids)

#Create a shapefile of the specified list of station IDs
NOAA.create_shapefile(station_ids, file_name="Stations.shp")