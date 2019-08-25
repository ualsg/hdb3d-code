#!/bin/env python

#-- a script to generate the building footprint (2D) from OSM 
#-- and enrich it with attributes from OSM and HDB, and estimate the height from the no. of storeys
#-- Filip Biljecki <filip@nus.edu.sg>
#-- 2019-08

import json
from shapely.geometry import Polygon, shape, mapping

with open('_data/blocks_coordinates.json', 'r') as f:
    blocks_coordinates = json.load(f)

with open('_data/osm_entry.json', 'r') as f:
    osm_entry = json.load(f)

print(len(blocks_coordinates), len(osm_entry))

#-- here goes the tricky part about heights...
#-- according to https://www.teoalida.com/singapore/hdbfloorplans/ the HDB floor-to-floor standard is 2.80 meters + 0.30 m for the top floor
#-- HDBs may have various constructions on the roof so later we add an additional 1.0m for that (so it's an additional 1.0 + 0.3 = 1.3 in total for each building)
#-- sorry, it's not exact science
#-- TODO: oh but that doesn't apply to multi-storey carparks, so those will need to be adjusted accordingly
storeyheight = 2.8

#-- iterate through the list of buildings and create GeoJSON features rich in attributes
footprints = {
    "type": "FeatureCollection",
    "features": []
    }
for i in osm_entry:
    f = {
    "type" : "Feature"
    }
    f["osm_id"] = osm_entry[i]["id"]
    f["properties"] = {}
    for p in osm_entry[i]["properties"]:
        #-- store all OSM attributes and prefix them with osm_
        f["properties"]["osm_%s" % p] = osm_entry[i]["properties"][p]
    osm_shape = shape(osm_entry[i]["geometry"])
    #-- a few buildings are not polygons, rather linestrings. This converts them to polygons
    #-- rare, but if not done it breaks the code later
    if osm_shape.type == 'LineString':
        osm_shape = Polygon(osm_shape)
    #-- there are also a few multipolygons. We'll take only the first one into account. TODO: make this smarter
    elif osm_shape.type == 'MultiPolygon':
        osm_shape = Polygon(osm_shape[0])
    #-- convert the shapely object to geojson
    f["geometry"] = mapping(osm_shape)
    #-- now store the HDB attributes
    hdb_attributes = blocks_coordinates[i]
    for att in hdb_attributes:
        #-- there are some attributes in that dictionary which we will not store
        if att[0:3] == "hdb":
            #-- all HDB attributes are prefixed with _hdb
            f["properties"][att] = hdb_attributes[att]
    #-- finally calculate the height and store it as an attribute (extrusion of geometry will be done in the next script)
    f["properties"]["height"] = float(hdb_attributes["hdb_max_floor_lvl"]) * storeyheight + 1.3
    footprints['features'].append(f)

#-- store the data as GeoJSON
with open('_data/footprints.geojson', 'w') as outfile:
    json.dump(footprints, outfile)
