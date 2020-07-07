###########
import buildings_from_osm
###########
print()
print("________________________________________")
print()
print("Part  2. Make df from json.")
from datetime import datetime
time_entry = "{:%H:%M:%S}".format(datetime.now())
print("time entry:", time_entry)
print("Please wait...")
print()

import os
import conda
conda_file_dir = conda.__file__
conda_dir = conda_file_dir.split('lib')[0]
proj_lib = os.path.join(conda_dir, 'Library\share')
# proj_lib = os.path.join(os.path.join(conda_dir, 'pkgs'), 'proj4-5.2.0-h6538335_1006\Library\share')
path_gdal = os.path.join(proj_lib, 'gdal')
os.environ ['PROJ_LIB']=proj_lib
os.environ ['GDAL_DATA']=path_gdal

# import networkx as nx
# import osmnx as ox
#import pandas as pd
#import geopandas as gpd
# import shapely
# from shapely.geometry import LineString, MultiLineString, Polygon, Point

# import wget
# import gdal, ogr
# import momepy
from datetime import datetime
import re
# import girs
# from girs.feat.layers import LayersReader
import overpass
from pyproj import Proj, transform

#отключить предупреждения pandas (так быстрее считает!!!):
#pd.options.mode.chained_assignment = None

import warnings
warnings.filterwarnings("ignore")

# api = overpass.API()

# minlat,minlon,maxlat,maxlon
# bbox=57.4553,39.2610,57.8433,40.4736

import time
import requests as req
import urllib.request

import shapely
from shapely.geometry import Point, LineString, MultiLineString, Polygon
import geopandas as gpd

################

bui_resp = buildings_from_osm.bui_resp
poly_resp = buildings_from_osm.poly_resp
path_raw_shp_poly = buildings_from_osm.path_raw_shp_poly
buff_km = buildings_from_osm.buff_km
place = buildings_from_osm.place
str_date = buildings_from_osm.str_date

################

###############
len_elem = len(bui_resp['elements'])
time_min = int(len_elem / 10000 / 60)
time_max = int(len_elem / 8000 / 60)

# time_start = "{:%H:%M:%S}".format(datetime.now())
# print("time start:", time_start)
print("Estimated time: {} to {} minutes".format(time_min,time_max))
###############

# getting polygon geometry
try:
    coords = []
    tags=[]
    osmid=[]
    for element in bui_resp['elements']:
        if element['type'] == 'way':
            one_line = []
            for j in range(len(element['geometry'])):
                lon = element['geometry'][j]['lon']
                lat = element['geometry'][j]['lat']
                one_line.append((lon, lat))
            coords.append(Polygon(one_line))
            try:
                tag = str(element['tags'])
            except:
                tag = None
            tags.append(tag)
            osmid.append(element['id'])
# 
except:
    pass
#


gdf_bui = gpd.GeoDataFrame(geometry=coords)
gdf_bui.crs='epsg:4326'

gdf_bui['tags'] = tags
gdf_bui['osm_id'] = osmid


##########################
# getting polygon geometry
try:
#     # Collect coords into list
    coords = []
    for element in poly_resp['elements']:
        if element['type'] == 'way':
            one_line = []
            for j in range(len(element['geometry'])):
                lon = element['geometry'][j]['lon']
                lat = element['geometry'][j]['lat']
                one_line.append((lon, lat))
            coords.append(LineString(one_line))
    #
    ml = MultiLineString(coords)
    buff_ml = ml.buffer(0.000000003)
    pl = ml.convex_hull
    diff = pl.difference(buff_ml)
    lst_len = []
    i=0
    max_ind = -1
    for i in range(len(diff)):
        len_poly = diff[i].length
        lst_len.append(len_poly)
        if len_poly == max(lst_len):
            max_ind = i
    # 
    boundary = diff[max_ind]
    gdf_poly=gpd.GeoDataFrame(geometry=[boundary])
    gdf_poly['osm_id'] = poly_osmid
    gdf_poly.crs='epsg:4326'
except:
    pass
#
if int(buff_km) > 0:
    buffer = int(buff_km) * 1000
    try:
        gdf_poly.crs = 'epsg:4326'
        gdf_poly.geometry = gdf_poly.geometry.to_crs('epsg:32637').buffer(buffer).to_crs('epsg:4326')
        gdf_poly.crs = 'epsg:4326'
    except:
        pass
#

########
# https://automating-gis-processes.github.io/site/notebooks/L3/spatial_index.html

def intersect_using_spatial_index(source_gdf, intersecting_gdf):
    """
    Conduct spatial intersection using spatial index for candidates GeoDataFrame to make queries faster.
    Note, with this function, you can have multiple Polygons in the 'intersecting_gdf' and it will return all the points
    intersect with ANY of those geometries.
    """
    source_sindex = source_gdf.sindex
    possible_matches_index = []

    # 'itertuples()' function is a faster version of 'iterrows()'
    for other in intersecting_gdf.itertuples():
        bounds = other.geometry.bounds
        c = list(source_sindex.intersection(bounds))
        possible_matches_index += c

    # Get unique candidates
    unique_candidate_matches = list(set(possible_matches_index))
    possible_matches = source_gdf.iloc[unique_candidate_matches]

    # Conduct the actual intersect
    result = possible_matches.loc[possible_matches.intersects(intersecting_gdf.unary_union)]
    return result
########

    # оставить только те ребра, которые внутри полигона
try:
    gdf_bui_tmp = intersect_using_spatial_index(gdf_bui, gdf_poly[['geometry']])
    gdf_bui_tmp = gdf_bui_tmp.reset_index(drop=True)
    # gdf_bui_tmp = gpd.sjoin(gdf_bui, gdf_poly[['geometry']], how='inner', 
                          # op='intersects').drop("index_right", axis=1).reset_index(drop=True)
    #
    if len(gdf_bui_tmp) > (len(gdf_bui) / 2):
        gdf_bui = gdf_bui_tmp.copy()
    gdf_bui_tmp = None
    #gdf_poly = None
    del gdf_bui_tmp#, gdf_poly
except:
    pass
#
#################

try:
    file_bui = '{}\\buildings_{}_{}_{}.shp'.format(path_raw_shp_poly,buff_km, place, str_date)
    gdf_bui.to_file(file_bui, encoding='utf-8')
except:
    print("Error, buildings.shp not saved")
#

try:
    file_poly = '{}\\poly_{}_{}_{}.shp'.format(path_raw_shp_poly,buff_km, place, str_date)
    gdf_poly.to_file(file_poly, encoding='utf-8')
except:
    print("Error, border.shp not saved")
#

time_end = "{:%H:%M:%S}".format(datetime.now())
print("time end:", time_end)
print("Done")