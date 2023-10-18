from noaa_ndbc import NOAA


NOAA.download(46022)
NOAA.download("46022")
NOAA.download([46022, "HBXC1"])
NOAA.download([46022, "HBXC1"], start=1995)
NOAA.download([46022, "HBXC1"], end=2010)
NOAA.download([46022, "HBXC1"], start=1995, end=2010)
NOAA.download([46022, "HBXC1"], dfs0=True)
NOAA.download([46022, "HBXC1"], dfs0=True, csv=False)
NOAA.download([46022, "HBXC1"], dfs0=True, csv=False, shapefile=True)
NOAA.download([46022, "HBXC1"], dfs0=True, csv=False, shapefile=True, shp_fname="Test1")
NOAA.download([46022, "HBXC1"], dfs0=True, csv=False, shapefile=True, shp_fname="Test2.shp")
NOAA.download(X=[-127, -124], Y=[40, 42])
NOAA.download(X=[-127, -124], Y=[40, 42], dfs0=True)
NOAA.download(X=[-127, -124], Y=[40, 42], dfs0=True, shapefile=True, shp_fname="Test3")

stations = [46022, 46002, "HBXC1", "HBYC1", "NJLC1"]
NOAA.download(X=[-127, -124], Y=[40, 42], dfs0=True, shapefile=True, shp_fname="Humboldt", csv=True)

