import json
import os
from datetime import datetime
import base64

from db import db, Park, Spot, Action, Shopping_item, User, Image
from flask import Flask, request, send_file, jsonify
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

# --------- Park Routes ------------
@app.route("/api/park/", methods=["POST"])
def create_park():
    body = json.loads(request.data)
    name = body.get("name")
    longitude = body.get("longitude")
    latitude = body.get("latitude")
    if name is None:
        return failure_response("Name is required!")
    if longitude is None:
        return failure_response("Longitute is required!")
    if latitude is None:
        return failure_response("Latitude is required!")
    park = Park(name=name, longitude=longitude, latitude=latitude)
    db.session.add(park)
    db.session.commit()
    return success_response(park.serialize(), 201)


@app.route("/api/park/")
def get_all_parks():
    parks = [park.serialize() for park in Park.query.all()]
    return success_response({"parks": parks})


@app.route("/api/park/<int:park_id>/")
def get_park_by_id(park_id):
    park = Park.query.filter_by(id=park_id).first()
    if park is None:
        return failure_response("Park not found!")
    return success_response(park.serialize())


@app.route("/api/park/<int:park_id>/", methods=["DELETE"])
def delete_park_by_id(park_id):
    park = Park.query.filter_by(id=park_id).first()
    if park is None:
        return failure_response("Park not found!")
    db.session.delete(park)
    db.session.commit()
    return success_response({})

# --------- Spot Routes ------------


@app.route("/api/park/<int:park_id>/spot/", methods=["POST"])
def create_spot(park_id):
    body = json.loads(request.data)
    name = body.get("name")
    longitude = body.get("longitude")
    latitude = body.get("latitude")
    suggester_id = body.get("suggester_id")

    if name is None or longitude is None or latitude is None:
        return failure_response("Name, longitude, and latitude are required!")

    if suggester_id is not None:
        suggester = User.query.filter_by(id=suggester_id).first()
        if suggester is None:
            return failure_response("Suggester not found!")
        spot = Spot(name=name, longitude=longitude,
                    latitude=latitude, park_id=park_id, suggester_id=suggester_id)
    else:
        spot = Spot(name=name, longitude=longitude,
                    latitude=latitude, park_id=park_id)

    db.session.add(spot)
    db.session.commit()
    return success_response(spot.serialize(), 201)


@app.route("/api/park/<int:park_id>/spot/")
def get_all_spots_by_park_id(park_id):
    spots = [spot.serialize()
             for spot in Spot.query.filter_by(park_id=park_id).all()]
    return success_response({"spots": spots})


@app.route("/api/spot/<int:spot_id>/")
def get_spot_by_id(spot_id):
    spot = Spot.query.filter_by(id=spot_id).first()
    if spot is None:
        return failure_response("Spot not found!")
    return success_response(spot.serialize())


@app.route("/api/spot/<int:spot_id>/", methods=["DELETE"])
def delete_spot_by_id(spot_id):
    spot = Spot.query.filter_by(id=spot_id).first()
    if spot is None:
        return failure_response("Spot not found!")
    db.session.delete(spot)
    db.session.commit()
    return success_response({})


@app.route("/api/spot/<int:spot_id>/image/", methods=["POST"])
def upload_spot_image(spot_id):
    image = request.files["image"]
    if image.filename == "":
        return failure_response("Image is required!")
    spot = Spot.query.filter_by(id=spot_id).first()
    if spot is None:
        return failure_response("Spot not found!")
    base64image = base64.b64encode(image.read()).decode("utf-8")
    image = Image(spot_id=spot_id, binary=base64image)
    spot.images_id.append(image)
    db.session.add(image)
    return success_response({})


@app.route("/api/spot/<int:spot_id>/image/")
def get_spot_image(spot_id):
    spot = Spot.query.filter_by(id=spot_id).first()
    if spot is None:
        return failure_response("Spot not found!")
    images = [image.binary() for image in spot.images_id]
    if not images:
        return failure_response("Images not found!")
    return jsonify(images)


@app.route("/api/spot/<int:spot_id>/action/", methods=["POST"])
def create_action(spot_id):
    body = json.loads(request.data)
    title = body.get("title")
    description = body.get("description")
    if title or description is None:
        return failure_response("Name and descrpition are required!")
    spot = Spot.query.filter_by(id=spot_id).first()
    if spot is None:
        return failure_response("Spot not found!")
    action = Action(name=title, spot_id=spot_id)
    db.session.add(action)
    db.session.commit()
    return success_response(action.serialize(), 201)

# --------- Users Routes ------------


@app.route("/api/users/")
def get_all_users():
    """
    Endpoint for getting all users
    """

    users = [user.simple_serialize() for user in User.query.all()]
    return success_response({"users": users})


@app.route("/api/users/", methods=["POST"])
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

    user = User.query.filter_by(username=username).first()

    if user is not None:
        return failure_response("user already exist", 400)

    user = User(username=username,
                password=hashed_password
                )

    db.session.add(user)
    db.session.commit()

    return success_response({"user_id": user.id}, 201)


@app.route("/api/users/<int:user_id>/")
def get_user_by_id(user_id):
    """
    Endpoint for getting user by id
    """
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("user not found")

    return success_response(user.serialize())


@app.route("/api/users/<int:user_id>/", methods=["DELETE"])
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


@app.route("/api/users/verify/", methods=["POST"])
def verify_user():
    """
    Endpoint for verifying whether password is correct
    """
    body = json.loads(request.data)
    username = body.get("username")
    password = body.get("password")

    if username is None or password is None:
        return failure_response("missing parameter", 400)

    user = User.query.filter_by(username=username).first()

    if user is None:
        return failure_response("user not found", 404)

    hashed_password = hash_password(password)

    # check with frontend for return message format

    if user.password == hashed_password:
        res = {
            "verify": True,
            "user_id": user.serialize().get("id")
        }
        return success_response(res)
    else:
        res = {"verify": False}
        return success_response(res, 403)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
