from flask import Flask
from sqlalchemy import create_engine


app = Flask(__name__)
app.config['SECRET_KEY'] = 'student'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:student@localhost/friend_rent'

engine = create_engine('postgresql://postgres:student@localhost/friend_rent')
conn = engine.connect()

from app import routes

