#!/bin/env python

#-- a script to associate the address of the building to the most likely corresponding building in OSM
#-- Filip Biljecki <filip@nus.edu.sg>
#-- 2019-08

import json
from shapely.geometry import Point, shape

#-- open the OSM dump
with open('_data/singapore-latest.geojson', 'r') as osm_file:
    osm_data = json.load(osm_file)['features']
print(len(osm_data))
osm_buildings = []
#-- filter out features that are not buildings
for f in osm_data:
    if 'building' in f['properties']:
        osm_buildings.append(f)
print(len(osm_buildings))

#-- load the geocoding data generated in the previous script
with open('_data/blocks_coordinates.json', 'r') as f:
    blocks_coordinates = json.load(f)

#-- create a new dictionary to store OSM data, or load the partially generated one (saves time if the script crashes)
try:
    with open('_data/osm_entry.json', 'r') as f:
        osm_entry = json.load(f)
    print("Loaded", len(osm_entry), "entries from previous file.")
except:
    osm_entry = {}

#-- counter
i = 0

for block in blocks_coordinates:
    print(block)
    #-- skip those already stored
    if str(i) in osm_entry:
        print("\tAlready fetched, skipping")
        i += 1
        continue
    else:
        i += 1
    #-- skip those blocks for which the address is not known
    if not blocks_coordinates[block]:
        continue
    #-- convert the lat/lon info into shapely Points
    point = Point(float(blocks_coordinates[block]['longitude']), float(blocks_coordinates[block]['latitude']))
    #-- find the nearest feature (usually we would use point in polygon, but some points from OneMap are outside the OSM polygon)
    d = 1000
    nearest = None
    #-- iterate all buildings and calculate distance. Yes, it's not the most efficient way. TODO: make it more efficient
    for b in osm_buildings:
        gj = b['geometry']
        osm_shape = shape(gj)
        try:
            d_ = osm_shape.distance(point)
            if d_ < d:
                d = d_
                nearest = b
                #-- if the point is in the polygon then the distance is zero, so let's just skip all other polygons
                if d == 0:
                    continue
        except:
            pass

    #-- save the most likely OSM footprint
    osm_entry[block] = nearest
    #-- save the file occasionally
    if i % 100 == 0:
        with open('_data/osm_entry.json', 'w') as f:
            json.dump(osm_entry, f)

with open('_data/osm_entry.json', 'w') as f:
    json.dump(osm_entry, f)