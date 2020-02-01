import json

from flask import Blueprint, request

from backend import db, bcrypt
from backend.models import User, Class, TeachingAssistant
from backend.users.utils import send_reset_email, token_expiration_json_response, insufficient_rights_json_response, \
    create_new_user, add_students

users = Blueprint('users', __name__)


@users.route('/login', methods=['POST'])
def login():
    """
    Enables log in verification and provides authentication token.
    Method Type
    -----------
    POST
    JSON Parameters
    ---------------
    email : str
        Email of the user
    password : str
        (Un-hashed) Password of the user
    Restrictions
    ------------
    User log in information must be correct
    JSON Returns
    ------------
    status : int
        Status code representing success status of the request
    message : str
        Message explaining the response status
    user : dict, optional
        Dictionary with information about the user
        id : int
            ID of the user
        auth_token : str
            Authentication token of the user
        name : str
            Name of the user
        email : str
            Email of the user
        access_level : int
            Access level of the user
    """
    request_json = request.get_json()
    email = request_json['email']
    password = request_json['password']
    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        user_info = {
            'id': user.id,
            'auth_token': user.get_auth_token(),
            'name': user.name,
            'email': user.email,
            'access_level': user.access_level
        }
        final_dict = {
            'user': user_info,
            'status': 0,
            'message': "Log in successful"
        }
        return json.dumps(final_dict)
    else:
        final_dict = {
            'status': 1,
            'message': "The provided combination of email and password is incorrect."
        }
        return json.dumps(final_dict)


@users.route('/register', methods=['POST'])
def normal_register():
    """
    Enables user registration by adding the user to the database.
    Method Type
    -----------
    POST
    JSON Parameters
    ---------------
    name : str
        name of the user
    email : str
        email of the user
    password : str
        (un-hashed) password of the user
    Restrictions
    ------------
    User must not already be registered
    JSON Returns
    ------------
    status : int
        Status code representing success status of the request
    message : str
        Message explaining the response status
    """
    request_json = request.get_json()
    name = request_json['name']
    email = request_json['email']
    password = request_json['password']
    creation_status = create_new_user(name=name, email=email, password=password)
    if not creation_status:
        return json.dumps({'status': 2, 'message': "User Already Exists"})
    return json.dumps({'status': 0, 'message': "User account created successfully"})


# End-point to enable a user to change their access level to administrator
@users.route('/admin/add', methods=['POST'])
def master_add():
    """
    Enables user conversion from normal to master user.
    Method Type
    -----------
    POST
    JSON Parameters
    ---------------
    email : str
        Email of the user
    Restrictions
    ------------
    User must be registered
    JSON Returns
    ------------
    status : int
        Status code representing success status of the request
    message : str
        Message explaining the response status
    """
    request_json = request.get_json()
    user = User.query.filter_by(email=request_json['email']).first()
    user.access_level = 4
    db.session.commit()
    return json.dumps({'status': 0})


# End-point to enable a user to request a new password
@users.route('/password/request_reset', methods=['GET', 'POST'])
def request_reset_password():
    request_json = request.get_json()
    user = User.query.filter_by(email=request_json['email']).first()
    if user:
        send_reset_email(user)
        return json.dumps({'status': 0, 'message': "Status Change Successful"})
    else:
        return json.dumps({'status': 1, 'message': "User Not Found"})


# End-point to enable a user to verify their password reset request
@users.route('/backend/password/verify_token', methods=['GET', 'POST'])
def verify_reset_token():
    request_json = request.get_json()
    user = User.verify_reset_token(request_json['token'])
    if user is None:
        return json.dumps({'status': 0,
                           'error': "Sorry, the link is invalid or has expired." +
                                    " Please submit password reset request again."})
    else:
        return json.dumps({'status': 1})


@users.route('/backend/password/reset', methods=['GET', 'POST'])
def reset_password():
    """
    Resets password of the user
    Method Type
    -----------
    POST
    JSON Parameters
    ---------------
    token : str
        Verification token to authenticate the user
    password : str
        New password of the user
    Restrictions
    ------------
    Verification token must not be expired
        Tokens expire 30 minutes after they are issued.
    JSON Returns
    ------------
    status : int
        Status code representing success status of the request
    message : str
        Message explaining the response status
    """
    request_json = request.get_json()
    user = User.verify_reset_token(request_json['token'])
    if user is None:
        return json.dumps({'status': 1,
                           'error': "Sorry, the link is invalid or has expired." +
                                    " Please submit password reset request again."})
    else:
        hashed_pwd = bcrypt.generate_password_hash(request_json['password']).decode('utf-8')
        user.password = hashed_pwd
        db.session.commit()
        return json.dumps({'status': 0, 'message': "Password Reset Successfully"})
