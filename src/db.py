from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

assoc_users_actions = db.Table(
    "association_users_actions",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("action_id", db.Integer, db.ForeignKey("action.id"))
)

assoc_actions_categories = db.Table(
    "association_actions_categories",
    db.Column("action_id", db.Integer, db.ForeignKey("action.id")),
    db.Column("category_id", db.Integer, db.ForeignKey("category.id")))


class User(db.Model):
    """
    User Model
    """

    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    points = db.Column(db.Integer, nullable=False, default=0)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    suggested_spots = db.relationship("Spot")
    volunteered_minutes = db.Column(
        db.Integer, nullable=False, default=0)
    actions = db.relationship(
        "Action", secondary=assoc_users_actions, back_populates="users")
    image = db.relationship("Image", cascade="delete", uselist=False)

    def __init__(self, **kwargs):
        """
        Initialize a user object
        """

        self.username = kwargs.get("username", "")
        self.password = kwargs.get("password", "")
        self.volunteered_minutes = 0

    def serialize(self):
        """
        Serialize a user object
        """
        return {
            "id": self.id,
            "username": self.username,
            "points": self.points,
            "actions": [action.simple_serialize() for action in self.actions],
            "suggested_spots": [spot.simple_serialize() for spot in self.suggested_spots]
        }

    def simple_serialize(self):
        """
        Serialize a user object without posts field
        """
        return {
            "id": self.id,
            "username": self.username
        }


class Park(db.Model):
    """
    Park Model
    """

    __tablename__ = "park"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    spots = db.relationship("Spot", cascade="delete")

    def __init__(self, **kwargs):
        """
        Initialize a park object
        """
        self.name = kwargs.get("name", "")
        self.longitude = kwargs.get("longitude", "")
        self.latitude = kwargs.get("latitude", "")

    def serialize(self):
        """
        Serialize a park object
        """
        return {
            "id": self.id,
            "name": self.name,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "spots": [spot.simple_serialize() for spot in self.spots]
        }

    def simple_serialize(self):
        """
        Serialize a park object without spots field
        """
        return {
            "id": self.id,
            "name": self.name,
            "longitude": self.longitude,
            "latitude": self.latitude
        }


class Spot(db.Model):
    """
    Spot Model
    """

    __tablename__ = "spot"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    park_id = db.Column(db.Integer, db.ForeignKey("park.id"), nullable=False)
    actions = db.relationship("Action", cascade="delete")
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    suggester_id = db.Column(
        db.Integer, db.ForeignKey("user.id"))
    images_id = db.relationship("Image", cascade="delete")

    def __init__(self, **kwargs):
        """
        Initialize a spot object
        """
        self.name = kwargs.get("name", "")
        self.longitude = kwargs.get("longitude", "")
        self.latitude = kwargs.get("latitude", "")
        self.park_id = kwargs.get("park_id", "")
        self.suggester_id = kwargs.get("suggester_id", 0)
        self.is_verified = kwargs.get("is_verified", False)

    def serialize(self):
        """
        Serialize a spot object
        """
        return {
            "id": self.id,
            "name": self.name,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "park_id": self.park_id,
            "park": Park.query.filter_by(id=self.park_id).first().name,
            "actions": [action.simple_serialize() for action in self.actions],
            "suggester_id": self.suggester_id,
            "is_verified": self.is_verified
        }

    def simple_serialize(self):
        """
        Serialize a spot object without actions field
        """
        return {
            "id": self.id,
            "name": self.name,
            "park": Park.query.filter_by(id=self.park_id).first().name,
            "longitude": self.longitude,
            "latitude": self.latitude
        }


class Action(db.Model):
    """
    Action Model
    """

    __tablename__ = "action"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey("spot.id"), nullable=False)
    users = db.relationship(
        "User", secondary=assoc_users_actions, back_populates="actions")
    images_id = db.relationship("Image", cascade="delete")
    categories = db.relationship(
        "Action_category", secondary=assoc_actions_categories, back_populates="actions")
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    time = db.Column(db.DateTime, nullable=False)
    minute_duration = db.Column(db.Integer, nullable=False, default=0)

    def __init__(self, **kwargs):
        """
        Initialize an action object
        """
        self.title = kwargs.get("title", "")
        self.description = kwargs.get("description", "")
        self.spot_id = kwargs.get("spot_id", "")
        self.is_verified = kwargs.get("is_verified", False)
        self.time = kwargs.get("time")
        self.minute_duration = kwargs.get("minute_duration", 0)

    def serialize(self):
        """
        Serialize an action object
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "spot_id": self.spot_id,
            "users": [user.simple_serialize() for user in self.users],
            "categories": [category.simple_serialize() for category in self.categories],
            "time": self.time,
            "is_verified": self.is_verified,
            "minute_duration": self.minute_duration
        }

    def simple_serialize(self):
        """
        Serialize an action object without spot field
        """
        return {
            "id": self.id,
            "title": self.title,
            "users": [user.simple_serialize() for user in self.users],
            "time": self.time,
            "is_verified": self.is_verified
        }


class Action_category(db.Model):
    """
    Action Category Model
    """

    __tablename__ = "category"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    point = db.Column(db.Integer, nullable=False)
    actions = db.relationship(
        "Action", secondary=assoc_actions_categories, back_populates="categories")

    def __init__(self, **kwargs):
        """
        Initialize an action category object
        """
        self.name = kwargs.get("name", "")
        self.point = kwargs.get("point", 0)

    def serialize(self):
        """
        Serialize an action category object
        """
        return {
            "id": self.id,
            "name": self.name,
            "actions": [action.simple_serialize() for action in self.actions],
            "point": self.point
        }

    def simple_serialize(self):
        """
        Serialize an action category object without actions field
        """
        return {
            "id": self.id,
            "name": self.name
        }


class Shopping_item(db.Model):
    """
    Shop Model
    """
    __tablename__ = "shopping_item"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String, nullable=False)
    image = db.relationship("Image", cascade="delete",
                            uselist=False)

    def __init__(self, **kwargs):
        """
        Initialize a shop object
        """
        self.name = kwargs.get("name", "")
        self.price = kwargs.get("price", "")
        self.description = kwargs.get("description", "")

    def serialize(self):
        """
        Serialize a shop object
        """
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "description": self.description,
            "image": self.image
        }


class Image(db.Model):
    """
    Image Model
    """
    __tablename__ = "image"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    binary = db.Column(db.String, nullable=False)
    shopping_item_id = db.Column(
        db.Integer, db.ForeignKey("shopping_item.id"))
    action_id = db.Column(db.Integer, db.ForeignKey("action.id"))
    spot_id = db.Column(db.Integer, db.ForeignKey("spot.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def init(self, **kwargs):
        """
        Initialize an image object
        """
        self.binary = kwargs.get("binary", "")

    def serialize(self):
        """
        Serialize an image object
        """
        return {
            "id": self.id,
            "binary": self.binary
        }

    def binary(self):
        """
        Return the binary data of the image
        """
        return self.binary
