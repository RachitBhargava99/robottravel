import json
from datetime import datetime
import requests

from flask import Blueprint, request, current_app

from backend import db
from backend.models import User, Tag
from backend.users.utils import token_expiration_json_response

import pprint

tags = Blueprint('tags', __name__)


# Checker to see whether or not is the ser ver running
@tags.route('/tag', methods=['GET'])
def queue_checker():
    return "Hello"


@tags.route('/tag/new', methods=['POST'])
def create_new_tag():
    """
    Creates new tag for the user

    Method Type
    -----------
    POST

    JSON Parameters
    ---------------
    auth_token : str
        Authentication of the logged in user
    keyword : str
        Keyword to create for the user

    Restrictions
    ------------
    User must be logged in
    Keyword must not already exist

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
    keyword = request_json['keyword']
    tag = Tag(keyword, user.id)
    db.session.add(tag)
    db.session.commit()
    return json.dumps({'status': 0, 'message': "User preference tag created successfully"})


@tags.route('/tag/del', methods=['POST'])
def delete_tag():
    """
    Deletes an existing tag for the user

    Method Type
    -----------
    POST

    JSON Parameters
    ---------------
    auth_token : str
        Authentication of the logged in user
    keyword_id : str
        Keyword to create for the user

    Restrictions
    ------------
    User must be logged in
    Keyword must exist
    Keyword must belong to the user

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
    keyword_id = request_json['keyword_id']
    tag = Tag.query.filter_by(id=keyword_id).first()
    if tag is None:
        return json.dumps({'status': 3, 'message': "Requested tag does not exist"})
    if tag.user_id != user.id:
        return json.dumps({'status': 3, 'message': "Requested tag does not belong to the user"})
    Tag.query.filter_by(id=keyword_id).delete()
    return json.dumps({'status': 0, 'message': "User preference tag deleted successfully"})
