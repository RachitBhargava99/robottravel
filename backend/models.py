from datetime import datetime

import itsdangerous
from flask import current_app
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from backend import db


class User(db.Model, UserMixin):
    """
    A database model class to store information about users.

    ...

    Attributes
    ----------
    id : int
        ID of the user object
    name : str
        Name of the user
    email : str
        Email of the user
    password : str
        (Hashed) Password of the user
    access_level : int
        Flag indicating the permission level of the user

    Methods
    -------
    get_auth_token(expires_seconds=86400)
        Generates a new authentication token for the user
    verify_auth_token(token)
        Verifies the provided authentication token for the user
    get_reset_token(expires_seconds=1800)
        Generates a new password reset token for the user
    verify_reset_token(token)
        Verifies the provided password reset token for the user
    """

    id = db.Column(db.Integer, primary_key=True)
    gt_id = db.Column(db.String(63), unique=False, nullable=False)
    access_level = db.Column(db.Integer, nullable=False, default=0)

    def __init__(self, gt_id: str, access_level: int = 0):
        """
        Parameters
        ----------
        gt_id : str
            (Hashed) Password of the user
        access_level : int
            Flag indicating the permission level of the user
        """
        self.gt_id = gt_id
        self.access_level = access_level

    def get_auth_token(self, expires_seconds: int = 3600) -> str:
        """
        Generates a new authentication token for the user.

        Parameters
        ----------
        expires_seconds : int, optional
            Number of seconds after which the token expires (default is 86400)

        Returns
        -------
        str
            The serialized authentication token to be returned to the user
        """
        s = Serializer(current_app.config['SECRET_KEY'], expires_seconds)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token: str):
        """
        Verifies the authentication token for the user.

        Parameters
        ----------
        token : str
            Serialized authentication token provided to verify the user's identity

        Returns
        -------
        User
            The User object corresponding to the provided authentication token
        """
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except itsdangerous.BadSignature:
            return None
        return User.query.get(user_id)

    def get_reset_token(self, expires_seconds: int = 1800) -> str:
        """
        Generates a new password reset token for the user.

        Parameters
        ----------
        expires_seconds : int, optional
            Number of seconds after which the token expires (default is 86400)

        Returns
        -------
        str
            The serialized password reset token to be returned to the user
        """
        s = Serializer(current_app.config['SECRET_KEY'], expires_seconds)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token: str):
        """
        Verifies the password reset token for the user.

        Parameters
        ----------
        token : str
            Serialized password reset token provided to verify the user's identity

        Returns
        -------
        User
            The User object corresponding to the provided password reset token
        """
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except itsdangerous.BadSignature:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User ID {self.id}"


class Class(db.Model):
    """
    A database model class to store information about users.

    ...

    Attributes
    ----------
    id : int
        ID of the class
    course_code : str
        Course Code
    course_name : str
        Course Name
    instructor_id : str
        Instructor ID, as stored in User table
    """

    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(31), nullable=False)
    course_name = db.Column(db.String(127), nullable=False)
    no_show_secs = db.Column(db.Integer, nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'), default=0, nullable=False)

    def __init__(self, code: str, name: str, instructor_id: int = 0, no_show_secs: int = 180):
        """
        Parameters
        ----------
        code : str
            Course Code
        name : str
            Course Name
        instructor_id : str
            Instructor ID, as stored in User table
        no_show_secs : int
            No Show Seconds for the course
        """
        self.course_code = code
        self.course_name = name
        self.instructor_id = instructor_id
        self.no_show_secs = no_show_secs


class Instructor(db.Model):
    """
    A database model class to store information about instructors

    ...

    Attributes
    ----------
    id : int
        ID of the teaching assistant
    user_id : int
        Instructor ID, as stored in User table
    course_id : int
        Course ID, as stored in Class table
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)

    def __init__(self, user_id, course_id):
        """
        Parameters
        ----------
        user_id : int
            Instructor ID, as stored in User table
        course_id : int
            Course ID, as stored in Class table
        """
        self.user_id = user_id
        self.course_id = course_id


class TeachingAssistant(db.Model):
    """
    A database model class to store information about teaching assistants

    ...

    Attributes
    ----------
    id : int
        ID of the teaching assistant
    user_id : int
        TA ID, as stored in User table
    course_id : int
        Course ID, as stored in Class table
    online : bool
        flag denoting whether or not is the TeachingAssistant online (on-duty)
    busy : bool
        flag denoting whether or not is the TeachingAssistant busy
    account_status : bool
        flag denoting whether or not is the account active
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    online = db.Column(db.Boolean, nullable=False, default=False)
    busy = db.Column(db.Boolean, nullable=False, default=False)
    account_status = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, user_id, course_id):
        """
        Parameters
        ----------
        user_id : int
            TA ID, as stored in User table
        course_id : int
            Course ID, as stored in Class table
        """
        self.user_id = user_id
        self.course_id = course_id
        self.online = False
        self.busy = False
        self.account_status = True


class Student(db.Model):
    """
    A database model class to store information about students

    ...

    Attributes
    ----------
    id : int
        ID of the student
    user_id : int
        Student ID, as stored in User table
    course_id : int
        Course ID, as stored in Class table
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)

    def __init__(self, user_id, course_id):
        """
        Parameters
        ----------
        user_id : int
            Student ID, as stored in User table
        course_id : int
            Course ID, as stored in Class table
        """
        self.user_id = user_id
        self.course_id = course_id


class QueuePosition(db.Model):
    """
    A database model class to store information about active queue entries

    ...

    Attributes
    ----------
    id : int
        ID of the student
    user_id : int
        Student ID, as stored in User table
    course_id : int
        Course ID, as stored in Class table
    status : bool
        Flag to denote whether or not is the student still in active queue
            0 -> Need Help
            1 -> Assigned to TA (waiting to show up)
            2 -> Assigned to TA
    timestamp : datetime
        DateTime indicating the last update date and time
    owner_id : int
        ID of User managing the QueuePosition (usually the TeachingAssistant)
            -1 denotes unassigned
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    queue_name = db.Column(db.String(63), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    status = db.Column(db.Integer, nullable=False, default=0)
    entry_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now())
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now())
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, default=-1)

    def __init__(self, user_id, queue_name, course_id):
        """
        Parameters
        ----------
        user_id : int
            Student ID, as stored in User table
        queue_name : str
            Queue Name to be used in the database to anonymize the user
        course_id : int
            Course ID, as stored in Class table
        """
        self.user_id = user_id
        self.queue_name = queue_name
        self.course_id = course_id
        self.status = 0
        self.entry_timestamp = datetime.now()
        self.timestamp = datetime.now()
        self.owner_id = -1


class Record(db.Model):
    """
    A database model class to store information about resolved / closed queue entries

    ...

    Attributes
    ----------
    id : int
        ID of the student
    opener_id : int
        Student ID, as stored in User table
    closer_id : int
        Student ID, as stored in User table
    course_id : int
        Course ID, as stored in Class table
    reason_code : int
        Reason code denoting the reason why the opener was removed from queue
            0 -> Resolved Normally
            1 -> Time Out
            2 -> Self-Removal
            3 -> No Show
            4 -> Requeue
    """
    id = db.Column(db.Integer, primary_key=True)
    opener_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    closer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    reason_code = db.Column(db.Integer, nullable=False, default=0)

    def __init__(self, opener_id, closer_id, course_id, reason_code):
        """
        Parameters
        ----------
        opener_id : int
            Student ID, as stored in User table
        closer_id : int
            Student ID, as stored in User table
        course_id : int
            Course ID, as stored in Class table
        reason_code : int
            Reason code denoting the reason why the opener was removed from queue
        """
        self.opener_id = opener_id
        self.closer_id = closer_id
        self.course_id = course_id
        self.reason_code = reason_code
