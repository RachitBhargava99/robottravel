from flask import Blueprint, request
from backend.models import User, Query
from backend.maps.utils import get_deviation_points, create_query
from backend import db
import json

webhooks = Blueprint('webhooks', __name__)


@webhooks.route('/incoming', methods=['POST'])
def get_webhook_request():
    request_json = request.get_json()

    print(request_json)

    intent = request_json['queryResult']['intent']['displayName']
    session_id = request_json['session']

    cat_to_num_dict = {
        'food': 1,
        'entertainment': 2,
        'clothing': 3,
        'bills': 4,
        'family': 5,
        'transportation': 6,
        'appliances': 7,
        'miscellaneous': 8
    }

    if intent == "Log In Prompt":
        email = request_json['queryResult']['parameters']['Email']
        user = User.query.filter_by(email=email).first()
        if user is None:
            message = "The user is not registered."
        else:
            user.slack_session = session_id
            db.session.commit()
            message = f"Welcome {user.name}! How can we help you?"

    elif intent == "Initial Input":
        user = User.query.filter_by(slack_session=session_id).first()
        if user is None:
            message = "Please log in."
        else:
            start = request_json['queryResult']['outputContexts'][0]['parameters']['Start.original']
            end = request_json['queryResult']['outputContexts'][0]['parameters']['End.original']
            if not create_query(start, end, user.id):
                message = "Query already exists"
            else:
                message = "Query created successfully - how many miles are you willing to travel before taking a break?"

    elif intent == "Add Threshold":
        user = User.query.filter_by(slack_session=session_id).first()
        if user is None:
            message = "The user is not registered."
        else:
            last_query = Query.query.filter_by(user_id=user.id).order_by(Query.id.desc()).first()
            threshold = request_json['queryResult']['parameters']['fd']
            last_query.fd = threshold
            db.session.commit()
            message = "Information updated - what would you be most interested in visiting in this trip?"

    elif intent == "Last Result":
        user = User.query.filter_by(slack_session=session_id).first()
        if user is None:
            message = "The user is not registered."
        else:
            last_query = Query.query.filter_by(user_id=user.id).order_by(Query.id.desc()).first()
            deviations = get_deviation_points(last_query.id)
            message = ', '.join([x['name'] for x in deviations])
            message = f"Suggested stopovers: {message}"

    else:
        message = "I am sorry, I did not get that."

    final_dict = {
        'fulfillmentText': message,
        'payload': {
            'google': {
                "expectUserResponse": True,
                "richResponse": {
                    "items": [
                        {
                            "simpleResponse": {
                                "textToSpeech": message,
                                "displayText": message
                            }
                        }
                    ]
                }
            },
            'facebook': {
                'text': message
            },
            'slack': {
                'text': message
            }
        },
    }

    print(final_dict)

    return json.dumps(final_dict)
