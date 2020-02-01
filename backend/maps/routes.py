import json
from datetime import datetime
import requests

from flask import Blueprint, request, current_app

from backend import db
from backend.models import User, Query, Location
from backend.users.utils import token_expiration_json_response, insufficient_rights_json_response
from backend.maps.utils import pathDeviationPoints

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
    new_query = Query(entry_o=entry_o, entry_d=entry_d, user_id=user.id)
    db.session.add(new_query)
    db.session.commit()
    return json.dumps({'status': 0, 'message': "User query created successfully"})


#Function to delete an existing query 
#using query_id and making sure of proper user
#Brandon Wand
@maps.route('/map/query/delete', methods=['POST'])
def delete_query():
    """
    Delete's a users query based on query_id

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
    return json.dumps({'status': 0, 'message': "User query created successfully"})


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
    deviations = pathDeviationPoints(polylines, 50, 'restaurant', 'american')
    # all_steps = direction_result['routes'][0]['legs'][0]['steps']
    # pp = pprint.PrettyPrinter()
    # pp.pprint(direction_result)
    return json.dumps({'status': 0, 'message': "Basic Route Created Successfully", 'start': query.entry_o,
                       'end': query.entry_d, 'deviations': deviations})


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
    location = Location(keyword=new_location, lat=lat, lng=lng, user_id=user.id)
    db.session.add(location)
    db.session.commit()
    return json.dumps({'status': 0, 'message': "Sponsor Location Added Successfully"})
