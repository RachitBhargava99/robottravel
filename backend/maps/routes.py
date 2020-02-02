import json
from datetime import datetime
import requests

from flask import Blueprint, request, current_app

from backend import db
from backend.models import User, Query, Location
from backend.users.utils import token_expiration_json_response, insufficient_rights_json_response
from backend.maps.utils import pathDeviationPoints, compute_deviation_points, get_deviation_points, create_query

import pprint

maps = Blueprint('maps', __name__)


# Checker to see whether or not is the ser ver running
@maps.route('/map', methods=['GET'])
def queue_checker():
    return "Hello"


@maps.route('/map/query/new', methods=['POST'])
def create_new_query():
    """
    Creates new query for the user

    Method Type
    -----------
    POST

    JSON Parameters
    ---------------
    auth_token : str
        Authentication of the logged in user
    entry_o : str
        Origin location entry from user
    entry_d : str
        Destination location entry from user

    Restrictions
    ------------
    User must be logged in

    JSON Returns
    ------------
    status : int
        Status code representing success status of the request
    message : str
        Message explaining the response status
    """
    request_json = request.get_json()
    auth_token = request_json['auth_token']
    user = User.verify_auth_token(auth_token)
    if user is None:
        return token_expiration_json_response
    entry_o = request_json['entry_o']
    entry_d = request_json['entry_d']
    create_query(entry_o=entry_o, entry_d=entry_d, user_id=user.id)
    return json.dumps({'status': 0, 'message': "User query created successfully"})


#Function to delete an existing query 
#using query_id and making sure of proper user
#Brandon Wand
@maps.route('/map/query/delete', methods=['POST'])
def delete_query():
    """
    Deletes a user's query based on query_id

    Method Type
    -----------
    POST

    JSON Parameters
    ---------------
    auth_token : str
        Authentication of the logged in user
    query_id : int
        ID of the query for which we need to

    Restrictions
    ------------
    User must be logged in
    Query must belong to the logged in user

    JSON Returns
    ------------
    status : int
        Status code representing success status of the request
    message : str
        Message explaining the response status
    polyline : str
        Polyline representing points to visit - to be used by Google Maps
    """
    #verify user
    request_json = request.get_json()
    auth_token = request_json['auth_token']
    user = User.verify_auth_token(auth_token)
    if user is None:
        return token_expiration_json_response 
    #grab query_id
    query_id = request_json['query_id']
    #check if query_id is empty
    if query_id is None:
        return json.dumps({'status': 3, 'message': "query_id is of type None"})
    query = Query.query.filter_by(id=query_id).first()
    #check if query is empty
    if query is None:
        return json.dumps({'status': 3, 'message': "query is of type None"})
    #make sure user id is the same as the query's user id
    if user.id != query.user_id:
        return json.dumps({'status': 3, 'message': "query does not belong to this user"})
    #delete the query
    query = Query.query.filter_by(id=query_id).delete()
    #commit to database
    db.session.commit()
    #output success message
    return json.dumps({'status': 0, 'message': "User query deleted successfully"})


@maps.route('/map/query/compute/<int:query_id>', methods=['GET'])
def compute_query_result(query_id: int):
    query = Query.query.filter_by(id=query_id).first()
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
    deviations = pathDeviationPoints(polylines, query.fd, ['restaurant', 'atm'], '')
    for curr_deviation in deviations:
        new_location = Location(keyword=curr_deviation['name'], lat=curr_deviation['lat'], lng=curr_deviation['lng'],
                                user_id=query.user_id, query_id=query.id)
        db.session.add(new_location)
        db.session.commit()
    return json.dumps({'status': 0, 'message': "Basic Route Created Successfully", 'deviations': deviations})


@maps.route('/map/query/result', methods=['POST'])
def create_query_result():
    """
    Creates new query for the user

    Method Type
    -----------
    POST

    JSON Parameters
    ---------------
    auth_token : str
        Authentication of the logged in user
    query_id : int
        ID of the query for which we need to

    Restrictions
    ------------
    User must be logged in
    Query must belong to the logged in user

    JSON Returns
    ------------
    status : int
        Status code representing success status of the request
    message : str
        Message explaining the response status
    polylines : str
        Polylines representing points to visit - to be used by Google Maps - one at a time
    """
    request_json = request.get_json()
    auth_token = request_json['auth_token']
    user = User.verify_auth_token(auth_token)
    if user is None:
        return token_expiration_json_response
    query_id = request_json['query_id']
    query = Query.query.filter_by(id=query_id).first()
    if query is None:
        return json.dumps({'status': 3, 'message': "Requested query does not exist"})
    deviations = get_deviation_points(query_id)
    # all_steps = direction_result['routes'][0]['legs'][0]['steps']
    # pp = pprint.PrettyPrinter()
    # pp.pprint(direction_result)
    return json.dumps({'status': 0, 'message': "Basic Route Created Successfully", 'start': query.entry_o,
                       'end': query.entry_d, 'deviations': deviations})


@maps.route('/map/query/get', methods=['GET', 'POST'])
def get_user_query():
    """
    Gets all the queries of the user.

    Method Type
    -----------
    POST

    JSON Parameters
    ---------------
    auth_token : str
        Authentication of the logged in user
    query_id : int
        ID of the query for which we need to

    Restrictions
    ------------
    User must be logged in
    Query must belong to the logged in user

    JSON Returns
    ------------
    status : int
        Status code representing success status of the request
    message : str
        Message explaining the response status
    queries : list(dict(str -> any))
        id : int
            ID of the query, as stored in database
        start : str
            Start point for the query
        end : str
            End point for the query
    """
    request_json = request.get_json()
    auth_token = request_json['auth_token']
    user = User.verify_auth_token(auth_token)
    if user is None:
        return token_expiration_json_response
    all_queries = Query.query.all()
    return json.dumps({'status': 0, 'message': "Request fulfilled successfully",
                       'queries': [{'id': x.id, 'start': x.entry_o, 'end': x.entry_d} for x in all_queries]})


@maps.route('/map/query/types', methods=['GET'])
def get_query_types():
    all_types = ["accounting", "airport", "amusement_park", "aquarium", "art_gallery", "atm", "bakery", "bank", "bar",
                 "beauty_salon", "bicycle_store", "book_store", "bowling_alley", "bus_station", "cafe", "campground",
                 "car_dealer", "car_rental", "car_repair", "car_wash", "casino", "cemetery", "church", "city_hall",
                 "clothing_store", "convenience_store", "courthouse", "dentist", "department_store", "doctor",
                 "drugstore", "electrician", "electronics_store", "embassy", "fire_station", "florist",
                 "funeral_home", "furniture_store", "gas_station", "grocery_or_supermarket", "gym", "hair_care",
                 "hardware_store", "hindu_temple", "home_goods_store", "hospital", "insurance_agency",
                 "jewelry_store", "laundry", "lawyer", "library", "light_rail_station", "liquor_store",
                 "local_government_office", "locksmith", "lodging", "meal_delivery", "meal_takeaway", "mosque",
                 "movie_rental", "movie_theater", "moving_company", "museum", "night_club", "painter", "park",
                 "parking", "pet_store", "pharmacy", "physiotherapist", "plumber", "police", "post_office",
                 "primary_school", "real_estate_agency", "rest_stop", "restaurant", "roofing_contractor", "rv_park",
                 "school", "secondary_school", "shoe_store", "shopping_mall", "spa", "stadium", "storage", "store",
                 "subway_station", "supermarket", "synagogue", "taxi_stand", "tourist_attraction", "train_station",
                 "transit_station", "travel_agency", "university", "veterinary_care", "zoo"]
    return json.dumps({'status': 0, 'message': "Queries Extracted Successfully", 'types': all_types})


@maps.route('/map/sponsor/loc/add', methods=['POST'])
def add_sponsor_location():
    """
    Adds a sponsor location to the database

    Method Type
    -----------
    POST

    JSON Parameters
    ---------------
    auth_token : str
        Authentication of the logged in user
    location : str
        Location to be added as sponsor location

    Restrictions
    ------------
    User must be logged in
    User must be a sponsor (access level = 1)

    JSON Returns
    ------------
    status : int
        Status code representing success status of the request
    message : str
        Message explaining the response status
    """
    request_json = request.get_json()
    auth_token = request_json['auth_token']
    user = User.verify_auth_token(auth_token)
    if user is None:
        return token_expiration_json_response
    if user.access_level < 1:
        return insufficient_rights_json_response
    new_location = request_json['location']
    place_search_raw_result = requests.post(f"{current_app.config['MAPS_PLACE_SEARCH_BASE']}?input={new_location}" +
                                            f"&inputtype=textquery" +
                                            f"&key={current_app.config['GCP_API_KEY']}")
    place_search_result = place_search_raw_result.json()
    lat = place_search_result['candidates'][0]['geometry']['location']['lat']
    lng = place_search_result['candidates'][0]['geometry']['location']['lng']
    location = Location(keyword=new_location, lat=lat, lng=lng, user_id=user.id, is_sp=True)
    db.session.add(location)
    db.session.commit()
    return json.dumps({'status': 0, 'message': "Sponsor Location Added Successfully"})


@maps.route('/map/sponsor/loc/delete', methods=['POST'])
def delete_location():
    """
    Deletes a sponsor location based on the sponsor_id

    Method Type
    -----------
    POST

    JSON Parameters
    ---------------
    auth_token : str
        Authentication of the logged in user
    location_id : int
        Location that needs to be deleted

    Restrictions
    ------------
    User must be logged in
    Location must belong to the logged in user

    JSON Returns
    ------------
    status : int
        Status code representing success status of the request
    message : str
        Message explaining the response status
    """
    request_json = request.get_json()
    auth_token = request_json['auth_token']
    user = User.verify_auth_token(auth_token)
    if user is None:
        return token_expiration_json_response
    location_id = request_json['location_id']
    loc = Location.query.filter_by(id=location_id).first()
    if loc is None:
        return json.dumps({'status': 3, 'message': "Location not found"})
    if user.id != loc.user_id:
        return json.dumps({'status': 3, 'message': "The requested location does not belong to this user"})
    Location.query.filter_by(id=location_id).delete()
    db.session.commit()
    return json.dumps({'status': 0, 'message': "Sponsor location deleted successfully"})


@maps.route('/map/ports/get', methods=['GET'])
def get_all_ports():
    """
    Gets all ports supported by Carnival

    Method Type
    -----------
    GET

    JSON Returns
    ------------
    status : int
        Status code representing success status of the request
    message : str
        Message explaining the response status
    ports : list(str)
        List of port names supported by Carnival
    """
    port_search_raw_data = requests.get(current_app.config['CARNIVAL_PORT_SEARCH_BASE'])
    port_search_data = port_search_raw_data.json()
    ports = [f"{curr_port['label']} Sea Port" for curr_port in port_search_data['options']['port']]
    return json.dumps({'status': 0, 'message': "Port Information Extracted Successfully", 'ports': ports})
