import json
import requests 
from geopy.distance import geodesic
from flask import current_app

#current_app.config['GCP_API_KEY'] 
API_KEY = 'AIzaSyDYUOtB-7CuX7Ex_BkbpOW4jP7redSjtTg' 
URL = ('https://maps.googleapis.com/maps/api/place/nearbysearch/json?')

#returns a dict of nearby lat and lng locations based on radius, latitude, longitude, type, and keywords/filters 
#see here for list of types https://developers.google.com/places/web-service/supported_types

def nearbyPlaces(rad, coord, typ, fil):
    p = {
        "location"  : "{}, {}".format(coord['lat'], coord['lng']),
        "radius"    : rad,
        "type"      : typ,
        "keyword"   : fil,
        "opennow"   : True,
        "key"       : API_KEY
    }
    response = requests.get(URL, params=p)
    print(response.status_code)
    if response.status_code != 200:
        print("Error, no response")
    else:
        jobj = response.json()
        results = jobj['results']
        coords = [ x ['geometry']['location'] for x in results]
        print(coords)
        return coords

#params:
#coords is of type dict { lat: float, long: float}
#base is a tuple of (lat, lon)
#return:
#type dict { lat: float, long: float}
#this takes in a dict of lat and lng locations and will return (lat and lng) the closest one to a base (int tuple)
def nearestCoord(coords, base):
    nearest = coords[0]
    min_dist = geodesic((nearest['lat'], nearest['lng']), base).miles
    for loc in coords:
        cur = (loc['lat'], loc['lng'])
        dist = geodesic(cur, base).miles
        if dist < min_dist:
            min_dist = dist
            nearest = loc
    return nearest



def nearbyPlace(coord, typ, fil):
    p = {
        "location"  : "{}, {}".format(coord['lat'], coord['lng']),
        "rankby"    : 'distance',
        "type"      : typ,
        "keyword"   : fil,
        "opennow"   : 'True',
        "key"       : API_KEY
    }
    response = requests.get(URL, params=p)
    print(response.status_code)
    if response.status_code != 200:
        print("Error, no response")
    else:
        jobj = response.json()
        res = jobj['results'][0]['geometry']['location']
        print(res)
        return res

#params:
#list of polylines made from tuples of (overall distance, list of coords)
#threshold value for deviation percentage (the higher the threshold the lower the deviation)
#radius of deviation, 
def pathDeviationPoints(pathData, threshold, typ, fil):
    #distance accumulator
    dist = 0
    points = []
    #loop through pathData
    for tup in pathData:
        #seperate tuples
        ov_dist = tup[0]
        coords = tup[1]
        #first check if ov_dist is greater than threshold
        if ov_dist > threshold or ov_dist+dist > threshold: 
            for pre, cur in zip(coords, coords[1:]):
                dist += geodesic(pre, cur).miles
                if dist >= threshold:
                    points.append(nearbyPlace(cur, typ, fil))
                    dist = 0
        else:
            #add the overall distance to the distance accumulator
            dist += ov_dist
    return points

coordst = nearbyPlace({'lat': 29.6, 'lng': -82.3}, "restaurant", "bbq")
