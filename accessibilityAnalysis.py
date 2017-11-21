# -*- coding: utf-8 -*-
"""
Created on Mon Nov 20 20:05:08 2017

@author: LY

Accessibility Analysis with Pandanas 
"""
import os 
import pandana
from pandana.loaders import osm
import fiona
import pandas as pd
import numpy as np 
import geopandas as gpd 

from unidecode import unidecode

os.chdir("D:\Documents\GitHub\UrbanForm")

#Decode unicode values in shapefile or this will give issues later
with fiona.open(os.path.join('data', 'points.shp'), 'r') as poi:
    
    #creating an ooutput shapefile with ISO-8859-1 encoding
    with fiona.open(os.path.join('data', 'points_unidecode.shp'), 'w', **poi.meta) as poi_decode:
        
        str_prop_keys = [k for k, v in poi_decode.schema['properties'].items() if v.startswith('str')]
        
        for rec in poi:
            
            for key in str_prop_keys:
                val = rec['properties'][key]
                if val:
                    rec['properties'][key] = unidecode(val)
                    
            poi_decode.write(rec)

#load file
coordinates = fiona.open(os.path.join('data', 'points_unidecode.shp'), 'r')
#Now to extract 1) Coordinates of points and 2) Type of points 
coord_dict = {}
for i in range(len(coordinates)):
        for k, v in coordinates[i]['geometry'].iteritems():
            if k == 'coordinates':
                coord_dict.setdefault(k, []).append(v)  

type_dict = {}
for i in range(len(coordinates)):
    for k, v in coordinates[i]['properties'].iteritems():
        if k == 'type':
            type_dict.setdefault(k, []).append(v)

#Join dictionaries
coord_dict = pd.DataFrame.from_dict(coord_dict)
type_dict = pd.DataFrame.from_dict(type_dict)

poi = pd.merge(type_dict, coord_dict, left_index=True, right_index=True)

#count number of unique POIs 
print len(poi.type.unique())

#that's way too many; let's try scaling down the type of amenities we are looking for 
#get list of amenities
amenity_list = []
for a in poi.type.unique():
    print amenity_list.append(a)
    
#there's dirty data in here
#for example,, what is "i", or "maze"? These are not amenities.
#furthermore, some of these amenities have too specific descriptions
#Let's decide on what amenities we want to take
#for now, let's do school, doctors, pharmacy, restaurants

amenities = ['restaurant', 'school', 'doctors', 'pharmacy']

poi = poi[poi['type'].isin(amenities)] #remove all amenities that are not in our shortlisted amenities

del poi #save space in memory for alt method 

##Alternative Method: as explained in the notebook here: https://github.com/gboeing/urban-data-science/blob/master/20-Accessibility-Walkability/pandana-accessibility-demo-full.ipynb
#the osm method from pandanas can be used to automatically retrieve POIs from open street map, instead of downloading from bbbike or geofabrik
#configuration of search: max distance 1km for up to 10 nearest POI
#This method seems a little less flexible than loading a shapefile however; I do not know what tags count as amenities
#With loading in a shapefile I can count transport "amenities" such as tube and bus stops too
distance = 1000
num_pois = 10
num_categories = len(amenities) + 1 #categories, one for each amenity + total


#bbox = min longitude, min latitude, max longitude, max latitude OR
#bbox = left, bottom, right, top 
bbox = [51.4925, -0.163422, 51.539502, -0.089264] #Bounding box of Central London (Mayfair, Soho, Clerkenwell)

####Specifications for visualisation####
#keyword arguments for matplotlib fig
bbox_aspect_ratio = (bbox[2] - bbox[0]) / (bbox[3] - bbox[1])
fig_kwargs = {'facecolor': 'w',
              'figsize': (10, 10 * bbox_aspect_ratio)}

#arguments for scatter plots
plot_kwargs = {'s': 5,
               'alpha': 0.9,
               'cmap': 'viridis_r', #reversed color map
               'edgecolor': 'none'}

#Network aggregation plots (no reversed color map)
agg_plot_kwargs = plot_kwargs.copy()
agg_plot_kwargs = plot_kwargs['cmap'] = 'viridis'

#keyword arguments for hex bin plots
hex_plot_kwargs = {'gridsize': 60,
                   'alpha': 0.9,
                   'cmap': 'viridis_r',
                   'edgecolor': 'none'}

#keyword arguments to pass to make colorbar
cbar_kwargs = {}

#keyword arguments to pass to basemap
bmap_kwargs = {}

#color to make background of axis
bgcolor = 'k'
 

#configuration of file names to store POIs in CSV 
bbox_string = '_'.join([str(x) for x in bbox])
net_filename = os.path.join('data', 'network_{}.h5'.format(bbox_string))
poi_filename = os.path.join('data', 'pois_{}_{}.csv'.format('_'.join(amenities), bbox_string)) 

if os.path.isfile(poi_filename):
    pois = pd.read_csv(poi_filename)
else:
    #get POIs directly from OSM 
    osm_tags = '"amenity"~"{}"'.format('|'.join(amenities))
    pois = osm.node_query(bbox[0], bbox[1], bbox[2], bbox[3], tags = osm_tags)
    
    #drop any types of POIs that do not fully match our list of amenities 
    pois = pois[pois['amenity'].isin(amenities)]
    pois.to_csv(poi_filename, index=False, encoding='utf-8')
    
    #sanity checking output
    print pois[['amenity', 'name', 'lat', 'lon']].head()

#Number of each POI we got
pois['amenity'].value_counts()

if os.path.isfile(net_filename):
    network = pandana.network.Network.from_hdf5(net_filename)
else:
    #load network directly from Overpass API
    #note that osm.network_from_bbox is depreciated in the newer version of pandanas
    network = osm.pdna_network_from_bbox(bbox[0], bbox[1], bbox[2], bbox[3]) 
    
    #identify nodes that are connected to fewer than a threshold of other nodes within a given distance
    #reflect: why is this important?
    #As Geoff explains,  this identifies nodes that may not be connected to the network - so we'll have to exclude them
    #it is not possible to modify a network in place, so they will have to be saved to HDF5 and reloaded when a change is made
    lcn = network.low_connectivity_nodes(impedance=1000, count=10, imp_name='distance')
    network.save_hdf5(net_filename, rm_nodes=lcn)


#Calculate accessibility 
#Precomputes reachable within specified maximum distance
network.precompute(distance + 1)

#initialize underlying C++ POI engine
network.init_pois(num_categories=num_categories, max_dist=distance, max_pois=num_pois)

#initialize a category for all amenities with locations specified by lat-long columns
network.set_pois(category='all', x_col=pois['lon'], y_col=pois['lat'])

#finds n closest amenities of each type to each node on the network
all_access = network.nearest_pois(distance=distance, category='all', num_pois=num_pois)

#What's returned is a df with number of columns = number of POIs requested
#Where each cell is the network distance from the specified node to each n pois
print all_access.head()


#Plot
#Note: for those who haven't downloaded it, Basemap is a dependency here
#Install with conda install Basemap - pip no longer works 
n = 1
bmap, fig, ax = network.plot(all_access[n], bbox=bbox, plot_kwargs=plot_kwargs, fig_kwargs=fig_kwargs, 
                             bmap_kwargs=bmap_kwargs, cbar_kwargs=cbar_kwargs)
ax.set_axis_bgcolor(bgcolor)
ax.set_title('Walking distance (m) to nearest amenity around Central London', fontsize=15)
fig.savefig(os.path.join('outputs', 'accessibility_all_central_london.png'), dpi=200, bbox_inches='tight')

