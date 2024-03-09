import json
import os
from datetime import datetime

from db import db, Park, Spot, Action, Shopping_item, User
from flask import Flask, request, send_file
from hashlib import pbkdf2_hmac
from dotenv import load_dotenv

app = Flask(__name__)
db_filename = "Warmer-Sun.db"

load_dotenv()
salting = os.environ.get("PASSWORD_SALT")
iterations = int(os.environ.get("NUMBER_OF_ITERATIONS"))

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)
with app.app_context():
    db.create_all()

#### HELPER METHODS ####


def hash_password(password):
    secret_password = pbkdf2_hmac(
        'sha384', password.encode(), salting.encode(), iterations)
    return secret_password


#### GENERALIZE RETURN ####
def success_response(body, code=200):
    return json.dumps(body), code


def failure_response(message, code=404):
    return json.dumps({"error": message}), code


@app.route("/")
def front_page():
    return "Hello! :D"


#### ROUTES ####

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)


#--------- Users Routes ------------
@app.route("/api/users/")
def get_all_users():
    """
    Endpoint for getting all users
    """

    users = [user.simple_serialize() for user in User.query.all()]
    return success_response({"users": users})


@app.route("/api/users/", methods = ["POST"])
def add_user():
    """
    Endpoint for adding users
    """
    
    body = json.loads(request.data)
    username = body.get("username")
    password = body.get("password")

    if username is None or password is None:
        return failure_response("missing parameter", 400)

    hashed_password = hash_password(password)

    user = User.query.filter_by(username = username).first()

    if user is not None:
        return failure_response("user already exist", 400)

    user = User(username = username,
                password = hashed_password
                )
    
    db.session.add(user)
    db.session.commit()

    return success_response({"user_id": user.id}, 201)

@app.route("/api/users/<int:user_id>/")
def get_user_by_id(user_id):
    """
    Endpoint for getting user by id
    """
    user = User.query.filter_by(id = user_id).first()
    if user is None:
        return failure_response("user not found")
    
    return success_response(user.serialize())

@app.route("/api/users/<int:user_id>/", methods = ["DELETE"])
def delete_user_by_id(user_id):
    """
    Endpoint for deleting an user by its id
    """

    user = User.query.filter_by(id=user_id).first()

    if user is None:
        return failure_response("user not found", 404)

    db.session.delete(user)
    db.session.commit()
    return success_response({})


@app.route("/api/users/verify/", methods = ["POST"])
def verify_user():
    """
    Endpoint for verifying whether password is correct
    """
    body = json.loads(request.data)
    username = body.get("username")
    password = body.get("password")

    if username is None or password is None:
        return failure_response("missing parameter", 400)

    user = User.query.filter_by(username = username).first()

    if user is None:
        return failure_response("user not found", 404)
    
    hashed_password = hash_password(password)
    
    #check with frontend for return message format
    

    if user.password == hashed_password:
        res = {
            "verify":True,
            "user_id": user.serialize().get("id")
            }
        return success_response(res)
    else:
        res = {"verify":False}
        return success_response(res, 403)