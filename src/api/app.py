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

app = Flask(__name__)

load_dotenv(join(dirname(__file__), "../../.env"))

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")

db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))


def jwt_required(f):
   @wraps(f)
   def decorator(*args, **kwargs):
      token = None
      if 'x-access-tokens' in request.headers:
         token = request.headers['x-access-tokens']

      if not token:
         return jsonify({'message': 'Missing token'})

      try:
         data = jwt.decode(token, app.config[SECRET_KEY])
         current_user = Users.query.filter_by(email=data['email']).first()
      except:
         return jsonify({'message': 'Invalid token'})

      return f(current_user, *args, **kwargs)
   return decorator


@app.route('/register', methods=['POST'])
def register():
   data = request.get_json()

   hashed_password = generate_password_hash(data['password'], method='sha256')

   user = Users(email=data['email'], password=hashed_password)
   db.session.add(user)
   db.session.commit()
   user_data = {"id": user.id, "email": user.email}

   return jsonify({'message': 'Registered successfully', "user": user_data})
