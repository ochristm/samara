#############################
import gdf_from_osm
#############################

print()
print("___________________________")
print("Part 3. Processing a graph (filtering and creating nodes)")
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

import pandas as pd
import numpy as np
from datetime import datetime
import geopandas as gpd
import shapely

#from tqdm.notebook import tqdm

# # В случе ошибки RuntimeError: b'no arguments in initialization list'
# # Если действие выше не помогло, то нужно задать системной переменной PROJ_LIB
# # явный путь к окружению по аналогии ниже
# Для настройки проекции координат, поменять на свой вариант


# os.environ ['PROJ_LIB']=r'C:\Users\popova_kv\AppData\Local\Continuum\anaconda3\Library\share'
# os.environ ['GDAL_DATA']=r'C:\Users\popova_kv\AppData\Local\Continuum\anaconda3\Library\share\gdal'


#import osmnx as ox
import re
import math

#отключить предупреждения pandas (так быстрее считает!!!):
pd.options.mode.chained_assignment = None

import warnings
warnings.filterwarnings("ignore")
from time import sleep
pause = 0.1
sleep(pause)
#######################

gdf_lines = gdf_from_osm.gdf_lines
#gdf_multilines = gdf_from_osm.gdf_multilines
str_date = gdf_from_osm.str_date
place = gdf_from_osm.place
buff_km = gdf_from_osm.buff_km
poly_osmid = gdf_from_osm.poly_osmid
# BORDERS!!!!!
gdf_poly = gdf_from_osm.gdf_poly
# gdf_poly = ox.gdf_from_place(place, which_result=2, buffer_dist=int(buff_km)*1000)
# gdf_poly.crs='epsg:4326'

len_gdf = len(gdf_lines)
pause = round(0.00007 * len_gdf, 1)

###############
#path_data = './data/'
#path_res = './data/'

path_data = '.\\data\\' + str(poly_osmid) + '\\' + str_date
path_res = path_data + '\\res'

path_res_edges = path_res
path_res_nodes = path_res
####################

###############
len_elem = len(gdf_lines)
time_min = int(len_elem / 125 / 60)
time_max = int(len_elem / 55 / 60)

time_start = "{:%H:%M:%S}".format(datetime.now())
print("time start:", time_start)
print("Estimated time: {} to {} minutes".format(time_min,time_max))
###############
sleep(pause)


#####################
def main(gdf_lines, gdf_poly):

	city_graph = gdf_lines#.copy()
	sleep(pause)


	lst_highway_notok = ['steps', 'pedestrian', 'footway', 'path', 'raceway', 'road', 'track', 'planned', 'proposed', 'cycleway']

	lst_ot_notok = ['access"=>"no','abandoned','grass','hiking', 'land',
					'leisure','mud','natural','piste','private','wood']

	lst_ot_dlt = ['admin_level','aeroway','attraction','building',
					'ferry','power','ice_road', 'leaf_type', 'proposed', 'planned']
	#


	city_graph = city_graph[
		(city_graph.waterway.isna())
		& (city_graph.aerialway.isna())
		& (city_graph.man_made.isna())
		& ((city_graph.barrier.isna()) | (city_graph['barrier'] == 'yes'))
		& (~city_graph['other_tags'].str.contains('|'.join(lst_ot_dlt), na=False))]
	#
	
	#################
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
		gdf_lines_tmp = intersect_using_spatial_index(city_graph, gdf_poly[['geometry']])
		gdf_lines_tmp = gdf_lines_tmp.reset_index(drop=True)
		# gdf_lines_tmp = gpd.sjoin(city_graph, gdf_poly[['geometry']], how='inner', 
							  # op='intersects').drop("index_right", axis=1).reset_index(drop=True)
		#
		if len(gdf_lines_tmp) > (len(city_graph) / 2):
			city_graph = gdf_lines_tmp.copy()
		gdf_lines_tmp = None
		gdf_poly = None
		del gdf_lines_tmp, gdf_poly
	except:
		pass
	#
	#################
	
	sleep(pause)
	
	np_cg2 = city_graph.to_numpy()
	ind_hw = list(city_graph.columns).index('highway')
	ind_oi = list(city_graph.columns).index('osm_id')
	ind_ot = list(city_graph.columns).index('other_tags')
	ind_nm = list(city_graph.columns).index('name')
	ind_zo = list(city_graph.columns).index('z_order')

	lst_type_road = []

	i=0
	for i in range(len(np_cg2)):
		str1 = str(np_cg2[i][ind_ot])
		
		if "railway" in str1:
			if "subway" in str1:
				lst_type_road.append("MTR")
			elif "tram" in str1:
				lst_type_road.append("TM")
			else:
				lst_type_road.append("RAIL")
		else:
			if np_cg2[i][ind_hw] in lst_highway_notok:
				lst_type_road.append("PED")
			elif any((c in str1) for c in lst_ot_notok):
				lst_type_road.append("PED")
			elif ((np_cg2[i][ind_hw] == 'service') | (np_cg2[i][ind_zo] == 0)) & (np_cg2[i][ind_nm] == None):
				lst_type_road.append("PED")
			else:
				lst_type_road.append("RN")
	#

	city_graph['type_road'] = lst_type_road


	return city_graph

#####################

graph_full = main(gdf_lines, gdf_poly)



sleep(pause)

#################################################



def saveMe(graph_full,str_date,place,buff_km,poly_osmid):
	print("saving...")

	graph_full_shp = graph_full.copy()
	np_gf = graph_full_shp.to_numpy()
	ind_ot = list(graph_full_shp.columns).index('other_tags')
	
	sleep(pause)
	
	# обрезать для сохранения в шейп
	lst_ot = []
	i=0
	for i in range(len(np_gf)):
		if len(str(np_gf[i][ind_ot])) > 254:
			lst_ot.append(np_gf[i][ind_ot][:254])
		else:
			lst_ot.append(np_gf[i][ind_ot])
	# 
	graph_full_shp['other_tags'] = lst_ot
	
	sleep(pause)

	graph_full_shp.to_file('{}\\new_graph_{}_{}_{}.shp'.format(path_res_edges,buff_km, place, str_date), encoding='utf-8')
#
sleep(pause)
saveMe(graph_full,str_date,place,buff_km,poly_osmid)

time_end = "{:%H:%M:%S}".format(datetime.now())
print("time end:", time_end)
print("Results are in folder 'res'")
print("Done")