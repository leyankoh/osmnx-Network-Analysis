# -*- coding: utf-8 -*-
"""
Created on Fri Nov 17 22:01:45 2017

@author: LY

Exploring the osmmnx package for network analysis
"""

import os 
import osmnx as ox

os.chdir("D:\Documents\GitHub\UrbanForm")

if os.path.isdir('outputs') is not True:
    os.mkdir('outputs')

#testing osmnx out
places = ox.gdf_from_places(['Botswana', 'Zambia', 'Zimbabwe'])
places = ox.project_gdf(places)
ox.save_gdf_shapefile(places)
ox.plot_shape(ox.project_gdf(places))

#for this to work, geometry must be POLYGON. The API sometimes returns POINT
#Possibly the more reliable way is using centroid coordinates if you require point data
city = ox.gdf_from_place('Singapore')
ox.plot_shape(ox.project_gdf(city)) 

#sample code from documentation - plots network from the given coordinates 
G = ox.graph_from_point((37.79, -122.41), distance=750, network_type='all')
ox.plot_graph(G)

#coordinates of raffles place MRT in singapore
#plot 4km around it 
sing = ox.graph_from_point((1.283877, 103.851528), distance=4000, network_type='all') 
sing = ox.project_graph(sing)
#save graph - note, the package immediately creates an 'Images" folder and saves it with the given filename
fig, ax = ox.plot_graph(sing, fig_height = 9, fig_width = 9, bgcolor = '#404040', save = True, filename="singapore",
                        edge_color = "#f2f2f2", edge_alpha=0.5, node_alpha = 0, margin = 0)


#This plots out the ENTIRE road network for Singapore. Warning, it takes VERY long to load
#Cool functionality, but it might be faster to slap the entire roads data from OSM into arc/qgis if using
#data on such a large scale
G = ox.graph_from_place('Singapore, Singapore')
ox.plot_graph(G)


#method only works IF gdf_from_place returns geometry as POINT. 
#this seems random depending on input for gdf_from_place - I'm not sure why 
gdf = ox.gdf_from_place('Povo, Italy')
point_geometry = gdf['geometry'].iloc[0]
center_point = (point_geometry.y, point_geometry.x)
G = ox.graph_from_point(center_point, distance=3000)
ox.plot_graph(G)


#According to documentation, I may also draw isochrone maps with osmnx 
#This is an amazing feature
#And I wish I found it while doing my dissertation

import geopandas as gpd
import networkx as nx
import matplotlib.pyplot as plt 
from shapely.geometry import Point
from descartes import PolygonPatch

#let's test this out
place = (51.507351, -0.127758) 
network_type = 'walk'
trip_times = [5, 10, 15, 20, 25]
travel_speed = 4.5 #km/h

trafalgar = ox.graph_from_point(place, network_type = network_type)


traf_nodes = ox.graph_to_gdfs(trafalgar, edges=False)
x, y = traf_nodes['geometry'].unary_union.centroid.xy
center_node = ox.get_nearest_node(trafalgar, (y[0], x[0]))
trafalgar = ox.project_graph(trafalgar) #don't skip this step or the projection will be all wrong! (results in distorded map)

#edge attributes for time in minutes required to traverse an edge
mpm = travel_speed * 1000/60 #meters per minute 
for u, v, k, data in trafalgar.edges(data=True, keys=True):
    data['time'] = data['length'] / mpm


##From here the code can be found in: https://github.com/gboeing/osmnx-examples/blob/master/notebooks/13-isolines-isochrones.ipynb
# get one color for each isochrone
iso_colors = ox.get_colors(n=len(trip_times), cmap='Reds', start=0.3, return_hex=True)

# color the nodes according to isochrone then plot the street network
node_colors = {}
for trip_time, color in zip(sorted(trip_times, reverse=True), iso_colors):
    subgraph = nx.ego_graph(trafalgar, center_node, radius=trip_time, distance='time')
    for node in subgraph.nodes():
        node_colors[node] = color
nc = [node_colors[node] if node in node_colors else 'none' for node in trafalgar.nodes()]
ns = [20 if node in node_colors else 0 for node in trafalgar.nodes()]
fig, ax = ox.plot_graph(trafalgar, fig_height=8, node_color=nc, node_size=ns, node_alpha=0.8, node_zorder=2) 

# make the isochrone polygons
isochrone_polys = []
for trip_time in sorted(trip_times, reverse=True):
    subgraph = nx.ego_graph(trafalgar, center_node, radius=trip_time, distance='time')
    node_points = [Point((data['x'], data['y'])) for node, data in subgraph.nodes(data=True)]
    bounding_poly = gpd.GeoSeries(node_points).unary_union.convex_hull
    isochrone_polys.append(bounding_poly)
    
# plot the network then add isochrones as colored descartes polygon patches
fig, ax = ox.plot_graph(trafalgar, fig_height=8, show=False, close=False, edge_color='k', edge_alpha=0.2, node_color='none')

for polygon, fc in zip(isochrone_polys, iso_colors):
    patch = PolygonPatch(polygon, fc=fc, ec='none', alpha=0.6, zorder=-1)
    ax.add_patch(patch)
plt.show()