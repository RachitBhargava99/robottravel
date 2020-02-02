import json
import requests 
import polyline
import random
from geopy.distance import geodesic
from flask import current_app
from threading import Thread
from google.cloud import pubsub_v1

from backend import db
from backend.models import Query, Location, Tag

# current_app.config['GCP_API_KEY']
API_KEY = 'AIzaSyDYUOtB-7CuX7Ex_BkbpOW4jP7redSjtTg' 
URL = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?'


# returns a dict of nearby lat and lng locations based on radius, latitude, longitude, type, and keywords/filters
# see here for list of types https://developers.google.com/places/web-service/supported_types
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
def nearestCoord(locations, base):
    locations.sort(key=lambda x: geodesic((x['lat'], x['lng']), base).miles + get_rating(x['place_id']) * 10)
    # nearest = coords[0]
    # min_dist = geodesic((nearest['lat'], nearest['lng']), base).miles
    # for loc in coords:
    #     cur = (loc['lat'], loc['lng'])
    #     dist = geodesic(cur, base).miles
    #     if dist < min_dist:
    #         min_dist = dist
    #         nearest = loc
    return locations[0]


def get_rating(place_id):
    raw_place_details = requests.get(current_app.config['MAPS_PLACE_DETAIL_BASE'],
                                     params={
                                         'key': current_app.config['GCP_API_KEY'],
                                         'place_id': place_id,
                                         'fields': 'rating'
                                     })
    place_details = raw_place_details.json()
    print(place_details)
    return place_details['result']['rating'] if place_details['result'].get('rating') is not None else 3.0


def nearbyPlace(coord, types, fil):
    results = []
    for typ in types:
        p = {
            "location"  : "{},{}".format(coord[0], coord[1]),
            "rankby"    : 'distance',
            "type"      : typ,
            "keyword"   : fil,
            "key"       : API_KEY
        }
        response = requests.get(URL, params=p)
        # print(response.json())
        if response.status_code != 200:
            print("Error, no response")
        else:
            jobj = response.json()
            if len(jobj['results']) == 0:
                continue
            res = []
            for x in jobj['results']:
                temp = x['geometry']['location']
                temp['place_id'] = x['place_id']
                temp['name'] = x['name'] + (', ' + x['formatted_address']
                                            if x.get('formatted_address') is not None else '')
                res.append(temp)
            results += res
    return results


# params:
# list of polylines made from tuples of (overall distance, list of coords)
# threshold value for deviation percentage (the higher the threshold the lower the deviation)
# radius of deviation,
def pathDeviationPoints(polylines, threshold, types, fil):
    sponsor_coordinates = [(x.lat, x.lng) for x in Location.query.all()]
    #distance accumulator
    dist = 0
    #deviation points and polyline points
    devpoints = []
    points = []
    #compile the polylines into one array of lats/lngs
    for line in polylines:
        points += polyline.decode(line)
    #accumulate distance and reset once threshold is reached
    for pre, cur in zip(points, points[1:]):
        dist += geodesic(pre, cur).miles
        if dist >= threshold:
            rand = random.random()
            flag = False
            if rand <= 0.2:
                for curr_sponsor in sponsor_coordinates:
                    if geodesic(cur, curr_sponsor).miles < 25:
                        devpoints.append(curr_sponsor)
                        dist = 0
                        flag = True
                        break
            if rand > 0.2 or not flag:
                dev_points = nearbyPlace(cur, types, fil)
                if len(dev_points) == 0:
                    dist *= 0.75
                    continue
                nearest_dev_point = nearestCoord(dev_points, cur)
                devpoints.append(nearest_dev_point)
                print(nearest_dev_point)
                dist = 0
    return devpoints


def compute_deviation_points(query):
    direction_raw_result = requests.post(f"{current_app.config['MAPS_DIRECTION_BASE']}?origin={query.entry_o}" +
                                         f"&destination={query.entry_d}&mode=driving" +
                                         f"&key={current_app.config['GCP_API_KEY']}")
    direction_result = direction_raw_result.json()
    base_leg = direction_result['routes'][0]['legs'][0]
    if base_leg.get('steps') is None:
        polylines = [base_leg['polyline']['points']]
    else:
        steps = base_leg['steps']
        polylines = [x['polyline']['points'] for x in steps]
    deviations = pathDeviationPoints(polylines, 25, ['restaurant', 'atm'], '')
    for curr_deviation in deviations:
        new_location = Location(keyword=curr_deviation['name'], lat=curr_deviation['lat'], lng=curr_deviation['lng'],
                                user_id=user.id, query_id=query.id)
        db.session.add(new_location)
        db.session.commit()
    return deviations


def get_deviation_points(query_id):
    print(query_id)
    all_deviation_points = [{'name': x.keyword, 'lat': x.lat, 'lng': x.lng} for x in
                            Location.query.filter_by(query_id=query_id, is_sp=False)]
    return all_deviation_points


def create_query(entry_o, entry_d, user_id, manual=False, keywords=['tourist_attraction', 'museum'], fd=50):
    old_query = Query.query.filter_by(entry_o=entry_o, entry_d=entry_d, user_id=user_id).first()
    if old_query is not None:
        return False
    new_query = Query(entry_o=entry_o, entry_d=entry_d, user_id=user_id, fd=fd)
    db.session.add(new_query)
    db.session.commit()
    new_query = Query.query.filter_by(entry_o=entry_o, entry_d=entry_d, user_id=user_id, fd=fd).first()
    for keyword in keywords:
        new_tag = Tag(keyword, new_query.id, user_id)
        db.session.add(new_tag)
    db.session.commit()
    if manual:
        publisher = pubsub_v1.PublisherClient()
        topic_name = 'projects/tester-267001/topics/compute-query'
        publisher.publish(topic_name, bytes(f"{new_query.id}", 'utf-8'))
    return True
    # parent = client.queue_path('thinger', 'us-east1', 'queue-blue')
    # task = {
    #     'app_engine_http_request': {
    #         'http_method': 'GET',
    #         'relative_uri': f'/map/query/compute/{new_query.id}',
    #         'app_engine_routing': {
    #             'service': 'worker'
    #         }
    #     }
    # }
    # response = client.create_task(parent, task)
    # eta = response.schedule_time.ToDateTime().strftime("%m/%d/%Y, %H:%M:%S")
    # print(f'Task {response.name} enqueued, ETA {eta}.')
