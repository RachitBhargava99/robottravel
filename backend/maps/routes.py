import json
from datetime import datetime

from flask import Blueprint, request

from backend import db
from backend.models import User, Student, QueuePosition, TeachingAssistant, Class, Instructor
from backend.queues.utils import dequeue_user, generate_random_queue_name
from backend.users.utils import token_expiration_json_response

maps = Blueprint('maps', __name__)


# Checker to see whether or not is the ser ver running
@maps.route('/map', methods=['GET'])
def queue_checker():
    return "Hello"
