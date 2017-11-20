# -*- coding: utf-8 -*-
"""
Created on Mon Nov 20 20:05:08 2017

@author: LY

Accessibility Analysis with Pandanas 
"""
import os 
import pandana
import time
import fiona
import pandas as pd
import numpy as np 
from pandana.loaders import osm
import pysal as ps

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
#for now, let's do school, doctors, pharmacy, restaurants and stops and bus stops

amenities = ['restaurant', 'school', 'doctors', 'pharmacy', 'stop', 'bus_stop']