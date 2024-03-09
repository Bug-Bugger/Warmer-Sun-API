import json
import os
from datetime import datetime

from db import db, Location, Feature, Post, User
from flask import Flask, request, send_file
from hashlib import pbkdf2_hmac
from dotenv import load_dotenv

app = Flask(__name__)
db_filename = "Warmer-Sun.db"

load_dotenv()
salting = os.environ.get("PASSWORD_SALT")
iterations = int(os.environ.get("NUMBER_OF_ITERATIONS"))
image_route(app)
weather_route(app)

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
@app.route("/api/park/", methods=["POST"])
def create_park():
    body = json.loads(request.data)
    name = body.get("name")
    if name is None:
        return failure_response("Name is required!")
    park = Park(name=name)
    db.session.add(park)
    db.session.commit()
    return success_response(park.serialize(), 201)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
