import fiona

def create_point_shapefile(lons, lats, labels=None, out_file="Shapefile.shp"):
    if len(lons) != len(lats):
        print("Length of lons and lats must be the same!")
        return None
    if labels == None:
        labels = [str(i) for i in range(len(lons))]
    
    schema = { 'geometry':'Point', 'properties':[('Name','str')]}
    fiona.supported_drivers
    pointShp = fiona.open(out_file, mode='w', driver='ESRI Shapefile', schema = schema, crs = "EPSG:4326")

    for i in range(len(labels)):
        rowDict = { 'geometry' : {'type':'Point', 'coordinates': (lons[i],lats[i])}, 'properties': {'Name' : str(labels[i])}}
        pointShp.write(rowDict)
    
    pointShp.close()

    print("Shapefile created!")
    return