import json
import os
import random
import string

from flask import url_for, current_app
from flask_mail import Message

from backend import mail, db, bcrypt
from backend.models import User

token_expiration_json_response = json.dumps({'status': 1, 'message': "User not logged in / Session expired"})

insufficient_rights_json_response = json.dumps({'status': 2, 'message': "Insufficient Rights"})

user_type_by_access = {
    0: "Normal User",
    1: "Teaching Assistant",
    2: "Course Instructor",
    3: "Admin",
    4: "Super-Admin"
}


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender=os.environ['MAIL_USERNAME'], recipients=[user.email])
    msg.body = f'''To reset your password, kindly visit: {url_for('users.reset', token=token, _external=True)}

Kindly ignore this email if you did not make this request'''
    mail.send(msg)
