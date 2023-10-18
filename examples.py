from noaa_ndbc import NOAA


#Download data for a single station in CSV format
NOAA.download(46022)
NOAA.download("46022")
#Download data for a group of stations in CSV format
NOAA.download([46022, "HBXC1"])
#Download data for a group of stations in CSV format starting 1995 (The start date will be replaced with the first available year in case it is after the specified year)
NOAA.download([46022, "HBXC1"], start=1995)
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
NOAA.download(X=[-127, -124], Y=[40, 42], dfs0=True, shapefile=True, shp_fname="Test3")
