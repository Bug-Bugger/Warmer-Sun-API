import json
import os
from datetime import datetime
import base64

from db import db, Park, Spot, Action, Shopping_item, User, Image, Action_category
from flask import Flask, request, send_file, jsonify
from hashlib import pbkdf2_hmac
from dotenv import load_dotenv
from flask_cors import CORS
from data_visualization import process_csv, create_heatmap

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*",
                                 "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                                 "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Credentials"]}})


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
    return json.dumps(body, default=str), code


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
                    latitude=latitude, park_id=park_id, is_verified=True)

    db.session.add(spot)
    db.session.commit()
    return success_response(spot.serialize(), 201)


@app.route("/api/spot/<int:spot_id>/verify/")
def verify_spot(spot_id):
    spot = Spot.query.filter_by(id=spot_id).first()
    if spot is None:
        return failure_response("Spot not found!")
    spot.is_verified = True
    db.session.commit()
    return success_response(spot.serialize(), 201)


@app.route("/api/park/<int:park_id>/spot/")
def get_all_spots_by_park_id(park_id):
    spots = [spot.serialize()
             for spot in Spot.query.filter_by(park_id=park_id, is_verified=True).all()]
    return success_response({"spots": spots})


@app.route("/api/spot/")
def get_all_spots():
    spots = [spot.serialize() for spot in Spot.query.all()]
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

# --------- Action Routes ------------


@app.route("/api/spot/<int:spot_id>/action/", methods=["POST"])
def create_action(spot_id):
    body = json.loads(request.data)
    title = body.get("title")
    description = body.get("description")
    users_name = body.get("users_name")
    categories = body.get("categories")
    minute_duration = body.get("minute_duration")
    if title is None or description is None:
        return failure_response("Name and descrpition are required!")
    spot = Spot.query.filter_by(id=spot_id).first()
    if users_name is None:
        return failure_response("Users name are required!")

    if spot is None:
        return failure_response("Spot not found!")
    if categories is None:
        return failure_response("Categories are required!")

    time = datetime.now()

    action = Action(title=title, description=description,
                    spot_id=spot_id, time=time, minute_duration=minute_duration)
    for category in categories:
        category = Action_category.query.filter_by(name=category).first()
        if category is None:
            return failure_response("Category not found!")
        action.categories.append(category)
    for user in users_name:
        user = User.query.filter_by(username=user).first()
        if user is None:
            return failure_response("User not found!")
        action.users.append(user)

    db.session.add(action)
    db.session.commit()
    return success_response(action.serialize(), 201)


@app.route("/api/action/<int:action_id>/", methods=["POST"])
def verify_action(action_id):
    action = Action.query.filter_by(id=action_id).first()
    if action is None:
        return failure_response("Action not found!")
    if action.is_verified:
        return failure_response("Action already verified!")
    action.is_verified = True
    max_base_points = max(category.points for category in action.categories)

    for user in action.users:
        user.points += max_base_points * action.minute_duration
        user.volunteered_minutes += action.minute_duration

    db.session.commit()
    return success_response(action.serialize(), 201)


@app.route("/api/action/")
def get_all_actions():
    actions = [action.serialize() for action in Action.query.all()]
    return success_response({"actions": actions})


@app.route("/api/spot/<int:spot_id>/action/")
def get_all_actions_by_spot_id(spot_id):
    actions = [action.serialize()
               for action in Action.query.filter_by(spot_id=spot_id).all()]
    return success_response({"actions": actions})


@app.route("/api/action/<int:action_id>/", methods=["DELETE"])
def delete_action_by_id(action_id):
    action = Action.query.filter_by(id=action_id).first()
    if action is None:
        return failure_response("Action not found!")
    db.session.delete(action)
    db.session.commit()
    return success_response({})


@app.route("/api/action/<int:action_id>/image/", methods=["POST"])
def add_action_image(action_id):
    images = request.files["images"]  # TODO load from list of images
    if images is None:
        return failure_response("Images are required!")

    action = Action.query.filter_by(id=action_id).first()
    if action is None:
        return failure_response("Action not found!")
    for image in images:
        if image.filename == "":
            return failure_response("Image is required!")
        base64image = base64.b64encode(image.read()).decode("utf-8")
        image = Image(action_id=action_id, binary=base64image)
        action.images_id.append(image)
        db.session.add(image)
    db.session.commit()
    return success_response({})


@app.route("/api/action/<int:action_id>/image/")
def get_action_image(action_id):
    action = Action.query.filter_by(id=action_id).first()
    images = []
    if action is None:
        return failure_response("Action not found!")
    for image in action.images_id:
        images.append(image.binary)
    return jsonify(images)

# --------- Category Routes ------------


@app.route("/api/category/", methods=["POST"])
def create_category():
    body = json.loads(request.data)
    name = body.get("name")
    point = body.get("point")
    if name is None or point is None:
        return failure_response("Name and point are required!", 400)
    if Action_category.query.filter_by(name=name).first() is not None:
        return failure_response("Category already exists!", 400)
    category = Action_category(name=name, point=point)
    db.session.add(category)
    db.session.commit()
    return success_response(category.serialize(), 201)


@app.route("/api/category/")
def get_all_categories():
    categories = [category.serialize()
                  for category in Action_category.query.all()]
    return success_response({"categories": categories})


@app.route("/api/category/<int:category_id>/")
def get_category_by_id(category_id):
    category = Action_category.query.filter_by(id=category_id).first()
    if category is None:
        return failure_response("Category not found!")
    return success_response(category.serialize())


@app.route("/api/category/<int:category_id>/", methods=["DELETE"])
def delete_category_by_id(category_id):
    category = Action_category.query.filter_by(id=category_id).first()
    if category is None:
        return failure_response("Category not found!")
    db.session.delete(category)
    db.session.commit()
    return success_response({})


@app.route("/api/category/<int:category_id>/action/")
def get_all_actions_by_category_id(category_id):
    if category_id is None:
        return failure_response("Category id is required!")
    category = Action_category.query.filter_by(id=category_id).first()
    if category is None:
        return failure_response("Category not found!")
    actions = [action.serialize() for action in category.actions]
    return success_response({"actions": actions})

# --------- Shopping Item Routes ------------


@app.route("/api/shopping_item/", methods=["POST"])
def create_shopping_item():
    body = json.loads(request.data)
    name = body.get("name")
    price = body.get("price")
    description = body.get("description")
    image = request.files["image"]
    image = Image(binary=base64.b64encode(image.read()).decode("utf-8"))

    if name is None or price is None or description is None:
        return failure_response("Name and price are required!")
    shopping_item = Shopping_item(
        name=name, price=price, description=description)
    shopping_item.image = image
    db.session.add(shopping_item)
    db.session.commit()
    return success_response(shopping_item.serialize(), 201)


@app.route("/api/shopping_item/")
def get_all_shopping_items():
    shopping_items = [shopping_item.serialize()
                      for shopping_item in Shopping_item.query.all()]
    return success_response({"shopping_items": shopping_items})

# --------- Users Routes ------------


@app.route("/api/users/")
def get_all_users():
    """
    Endpoint for getting all users
    """

    users = [user.simple_serialize() for user in User.query.all()]
    return success_response({"users": users})


@app.route("/api/users", methods=["POST"])
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


@app.route("/api/users/<string:username>/")
def get_user_by_username(username):
    """
    Endpoint for getting user by username
    """
    user = User.query.filter_by(username=username).first()
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

    if user.password == hashed_password:
        res = {
            "verify": True,
            "user_id": user.serialize().get("id")
        }
        return success_response(res)
    else:
        res = {"verify": False}
        return success_response(res, 403)


@app.route('/api/analyze', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file:
        data = process_csv(file)
        heatmap_file = create_heatmap(data)
        return send_file(heatmap_file, mimetype='text/html')
    return 'No file received', 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
