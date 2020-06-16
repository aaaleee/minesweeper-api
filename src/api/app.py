import datetime
import uuid
import os
import jwt

from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from flask_swagger import swagger
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from os.path import join, dirname
from dotenv import load_dotenv

from marshmallow import ValidationError
from schemas.user_registration import UserRegistration
from schemas.authentication import Authentication
from schemas.cell_action import CellAction
from schemas.game_settings import GameSettings
from sqlalchemy.exc import IntegrityError

from models import db, User, Game
from services.game_service import GameService, InvalidClearException
from exceptions import InvalidClearException, GameNotFoundException, InvalidGameSettingsException

app = Flask(__name__)

load_dotenv(join(dirname(__file__), "../../.env"))

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")

db.init_app(app)
CORS(app)

def jwt_required(f):
   @wraps(f)
   def decorator(*args, **kwargs):
      token = None
      if "x-access-tokens" in request.headers:
         token = request.headers["x-access-tokens"]

      if not token:
         return jsonify({"message": "Missing token."})

      try:
         algos = jwt.algorithms.get_default_algorithms()
         data = jwt.decode(token, key=app.config["SECRET_KEY"], algorithms=algos)
         current_user = User.query.filter_by(email=data["email"]).first()
      except:
         return {"message": "Invalid token."}, 401

      return f(current_user, *args, **kwargs)
   return decorator

def find_game(user_id: int, game_id: int):
   game = Game.query.filter(and_(Game.id==game_id, Game.user_id==user_id)).first()
   if not game:
      raise GameNotFoundException(None, f"Game with ID {game_id} not found.")
   return game

@app.route("/register", methods=["POST"])
def register():
   """
   Add a user
   swagger_from_file: src/swagger/user_register.yml
   """
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
   """
   Authenticate
   swagger_from_file: src/swagger/user_authenticate.yml
   """
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


@app.route("/games", methods=["POST"])
@jwt_required
def new_game(current_user):
   """
   Start a new game
   swagger_from_file: src/swagger/game_start.yml
   """
   data = request.get_json()
   schema = GameSettings()

   try:
      settings = schema.load(data)
   except ValidationError as err:
      return jsonify(err.messages), 400

   rows = settings["rows"]
   columns = settings["columns"]
   mines =  settings["mines"]
   
   service = GameService()
   try:
      service.start_game(current_user.id, rows, columns, mines)
      db.session.add(service.game)
      db.session.commit()
   except InvalidGameSettingsException as exc:
      return jsonify({"message": str(exc)}), 400
   
   return jsonify(service.encode_game_info())

@app.route("/games/<id>", methods=["GET"])
@jwt_required
def retrieve_game(current_user, id):
   """
   Retrieve an existing game
   swagger_from_file: src/swagger/game_retrieve.yml
   """
   try:
      game = find_game(current_user.id, id)
      service = GameService(game)
   except GameNotFoundException as gnf:
      return jsonify({"message": str(gnf)}), 404

   return jsonify(service.encode_game_info())


@app.route("/games", methods=["GET"])
@jwt_required
def list_games(current_user):
   """
   List existing games for the current user
   swagger_from_file: src/swagger/game_list.yml
   """
   games = Game.query.filter_by(user_id=current_user.id).all()
   all_games = []
   for game in games:
      all_games.append({"id": game.id, "status": game.status})
   return {"games": all_games}


@app.route("/games/<id>/clear", methods=["POST"])
@jwt_required
def clear(current_user, id):
   """
   Clear a cell
   swagger_from_file: src/swagger/game_clear_cell.yml
   """
   data = request.get_json()
   schema = CellAction()
   try:
      game = find_game(current_user.id, id)
      service = GameService(game)
   except GameNotFoundException as gnf:
      return jsonify({"message": str(gnf)}), 404

   try:
      coords = schema.load(data)
   except ValidationError as err:
      return jsonify(err.messages), 400
   
   try:
      service.clear(coords["row"], coords["column"])
      game = service.game
      update_data = {
         "start_time": game.start_time,
         "end_time": game.end_time,
         "board": game.board,
         "status": game.status,
         "mines_left": game.mines_left
      }
      db.session.query(Game).filter(and_(Game.id==id, Game.user_id==current_user.id)).update(update_data)
      db.session.commit()
   except InvalidClearException as exc:
      return jsonify({"message": str(exc)}), 400
   
   return jsonify(service.encode_game_info())


@app.route("/games/<id>/toggle", methods=["POST"])
@jwt_required
def toggle(current_user, id):
   """
   Toggle a cell's status
   swagger_from_file: src/swagger/game_toggle_cell.yml
   """
   data = request.get_json()
   schema = CellAction()
   try:
      game = find_game(current_user.id, id)
      service = GameService(game)
   except GameNotFoundException as gnf:
      return jsonify({"message": str(gnf)}), 404

   try:
      coords = schema.load(data)
   except ValidationError as err:
      return jsonify(err.messages), 400
   
   try:
      service.toggle(coords["row"], coords["column"])
      st = service.game.start_time
      board = service.game.board
      db.session.query(Game).update({"start_time": st, "board": board})
      db.session.commit()
   except InvalidClearException as exc:
      return jsonify({"message": str(exc)}), 400
   
   return jsonify(service.encode_game_info())

@app.route("/spec")
def spec():
    swag = swagger(app, from_file_keyword='swagger_from_file')
    swag['info']['version'] = "1.0"
    swag['info']['title'] = "Mine Sweeper API"
    return jsonify(swag)