import json
from datetime import datetime
import requests

from flask import Blueprint, request, current_app

from backend import db
from backend.models import User, Query
from backend.users.utils import token_expiration_json_response

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


# TODO: Create a function to delete an existing query - use query_id and make sure that no other user can delete
#  other people's queries


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
    polyline : str
        Polyline representing points to visit - to be used by Google Maps
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
                                         f"&key=AIzaSyDYUOtB-7CuX7Ex_BkbpOW4jP7redSjtTg")
    direction_result = direction_raw_result.json()
    polyline = direction_result['routes'][0]['legs'][0]['polyline']['points']
    return json.dumps({'status': 0, 'message': "Basic Route Created Successfully", 'polyline': polyline})
