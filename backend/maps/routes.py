import json
from datetime import datetime

from flask import Blueprint, request

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
    User must be a student in the class

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
