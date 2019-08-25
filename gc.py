#!/bin/env python

#-- a script to fetch coordinates of each building
#-- Filip Biljecki <filip@nus.edu.sg>
#-- 2019-08

import pandas as pd
import json
import time
import requests

# Read the HDB data from the CSV
blocks = pd.read_csv('../../Data/datagovsg/hdb-property-information/hdb-property-information.csv', sep=',')

#-- create a new dictionary with block id, address, and coordinate; or load a previous one if generated
try:
    with open('_data/blocks_coordinates.json', 'r') as f:
        blocks_coordinates = json.load(f)
    print("Loaded", len(blocks_coordinates), "entries from previous file.")
except:
    blocks_coordinates = {}

#-- list of HDB attributes we have in the CSV
all_att = ['blk_no',
    'street',
    'max_floor_lvl',
    'year_completed',
    'residential',
    'commercial',
    'market_hawker',
    'miscellaneous',
    'multistorey_carpark',
    'precinct_pavilion',
    'bldg_contract_town',
    'total_dwelling_units',
    '1room_sold',
    '2room_sold',
    '3room_sold',
    '4room_sold',
    '5room_sold',
    'exec_sold',
    'multigen_sold',
    'studio_apartment_sold',
    '1room_rental',
    '2room_rental',
    '3room_rental',
    'other_room_rental'
    ]


#-- counter
ids = 0

#-- for each block
for i, j in blocks.iterrows():
    ids += 1
    #-- by default there is no location
    location = None
    #-- count how many features that are buildings are returned
    h = 0
    #-- construct the address for the geocoding API
    address = str(j['blk_no']) + ' ' + str(j['street'])
    print(i, '\t', str(j['blk_no']) + ' ' + str(j['street']))
    if i in blocks_coordinates:
        print("\tAlready fetched, skipping")
        continue

    #-- geocoder query
    for attempt in range(10):
        #-- max. 250 requests per second are allowed, so let's pause every 10ms not to exceed 100 requests per second
        time.sleep(0.010)
        try:
            #-- fetch the location of the block
            #-- no authentication isneeded for this functionality of the API
            response = requests.get('https://developers.onemap.sg/commonapi/search?searchVal=%s&returnGeom=Y&getAddrDetails=Y' % (address), auth=('user', 'password'))
            location = response.json()
            #-- thank you OneMap
        except:
            continue
        else:
            break
    else:
        print('10 attempts failed')

    if location:
        print('\tThere are', location['found'], 'result(s)')
        if location['found'] == 0:
            #-- if nothing is found (rarely happens)
            blocks_coordinates[i] = None
            continue
        #-- we are feeling lucky so we will just take the first result into consideration
        l = location['results'][0]
        #-- save the information
        blocks_coordinates[i] = {
            'blk_no' : str(j['blk_no']),
            'street' : str(j['street']),
            'address' : address,
            'latitude' : l['LATITUDE'],
            'longitude' : l['LONGITUDE']
            }
        #-- save the HDB attributes
        for att in all_att:
            blocks_coordinates[i]['hdb_'+att] = str(j[att])

    else:
        print('Address not found')
        blocks_coordinates[i] = None

    #-- this may take some time, so let's save the data occasionally
    if ids % 100 == 0:
        with open('_data/blocks_coordinates.json', 'w') as f:
            json.dump(blocks_coordinates, f)

with open('_data/blocks_coordinates.json', 'w') as f:
        json.dump(blocks_coordinates, f)