import datetime
import uuid
import os
import jwt

from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from os.path import join, dirname
from dotenv import load_dotenv

from marshmallow import ValidationError
from schemas.user_registration import UserRegistration
from schemas.authentication import Authentication
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

load_dotenv(join(dirname(__file__), "../../.env"))

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")

db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))

class Game(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   user_id = db.Column(db.Integer, nullable=False)
   rows = db.Column(db.Integer, nullable=False)
   columns = db.Column(db.Integer, nullable=False)
   mines_left = db.Column(db.Integer, nullable=False)
   start_time = db.Column(db.DateTime)
   status = db.Column(db.Enum("Started", "Won", "Lost"), nullable=False, default="Started")
   board = db.Column(db.JSON, nullable=False)


def jwt_required(f):
   @wraps(f)
   def decorator(*args, **kwargs):
      token = None
      if "x-access-tokens" in request.headers:
         token = request.headers["x-access-tokens"]

      if not token:
         return jsonify({"message": "Missing token."})

      try:
         data = jwt.decode(token, app.config[SECRET_KEY])
         current_user = Users.query.filter_by(email=data["email"]).first()
      except:
         return jsonify({"message": "Invalid token."})

      return f(current_user, *args, **kwargs)
   return decorator


@app.route("/register", methods=["POST"])
def register():
   data = request.get_json()
   schema = UserRegistration()

   try:
      result = schema.load(data)
   except ValidationError as err:
      return jsonify(err.messages), 400

   hashed_password = generate_password_hash(data["password"], method="sha256")

   try:
      user = Users(email=data["email"], password=hashed_password)
      db.session.add(user)
      db.session.commit()
      user_data = {"id": user.id, "email": user.email}
      return jsonify({"message": "Registered successfully", "user": user_data})
   except IntegrityError as err:
      return {"email": "That email is already registered."}, 400


@app.route("/authenticate", methods=["POST"])
def authenticate():
   data = request.get_json()
   schema = Authentication()

   try:
      result = schema.load(data)
   except ValidationError as err:
      return jsonify(err.messages), 400
   
   user = Users.query.filter_by(email=data["email"]).first()
   if user and check_password_hash(user.password,data["password"]):
      token = jwt.encode({'email': user.email, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(days=30)}, app.config['SECRET_KEY'])
      return {'token' : token.decode('UTF-8')}
   else:
      return {"message": "Authentication failed."}, 401