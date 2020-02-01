import json
import os
import random
import string

from flask import url_for, current_app
from flask_mail import Message

from backend import mail, db, bcrypt
from backend.models import User, Class, Student

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


def create_new_user(gt_id: str, access_level: int = 0) -> bool:
    """
    Creates a new user.

    Restrictions
    ------------
    User must not already exist - checked by email

    Parameters
    ----------
    gt_id : str
        name of the user
    access_level : int
        access level of the user

    Returns
    -------
    bool
        flag representing whether or not was the user creation successful
    """
    if check_existing_account(gt_id=gt_id)[1] is not None:
        return False
    hashed_gt_id = bcrypt.generate_password_hash(gt_id).decode('utf-8')
    user = User(gt_id=hashed_gt_id, access_level=access_level)
    db.session.add(user)
    db.session.commit()
    # print(os.environ.get('MAIL_PASSWORD'))
    return True


def add_students(student_list: list, course_id: int) -> bool:
    """
    Adds a list of students to the given course

    Restrictions
    ------------
    Course ID must be valid

    Parameters
    ----------
    student_list : list
        list of GT ID of students to be added
    course_id : int
        Course ID, as stored in Class database table

    Returns
    -------
    bool
        flag representing whether or not was the user creation successful
    """
    course = Class.query.filter_by(id=course_id).first()
    if course is None:
        return False
    # print(course_id, student_list)
    for st_gt_id in student_list:
        _, st = check_existing_account(st_gt_id)
        if st is None:
            create_new_user(gt_id=st_gt_id)
            _, st = check_existing_account(gt_id=st_gt_id)
        if Student.query.filter_by(id=st.id, course_id=course_id).first() is None:
            new_student = Student(user_id=st.id, course_id=course_id)
            db.session.add(new_student)
    db.session.commit()
    return True


def check_existing_account(gt_id: str):
    """
    Checks if a GT ID has an account

    Parameters
    ----------
    gt_id : str
        GT ID to check

    Returns
    -------
    (bool, User)
        bool
            representing whether or not a GT ID exists
        User
            User instance, if GT ID is already in the database; None otherwise
    """
    all_users = User.query.all()
    for curr_user in all_users:
        if bcrypt.check_password_hash(curr_user.gt_id, gt_id):
            return True, curr_user
    return False, None
