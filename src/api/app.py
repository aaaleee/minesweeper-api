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

from models import db, User, Game

app = Flask(__name__)

load_dotenv(join(dirname(__file__), "../../.env"))

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")

db.init_app(app)

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
         current_user = User.query.filter_by(email=data["email"]).first()
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
      user = User(email=data["email"], password=hashed_password)
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
   
   user = User.query.filter_by(email=data["email"]).first()
   if user and check_password_hash(user.password,data["password"]):
      token = jwt.encode({'email': user.email, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(days=30)}, app.config['SECRET_KEY'])
      return {'token' : token.decode('UTF-8')}
   else:
      return {"message": "Authentication failed."}, 401
