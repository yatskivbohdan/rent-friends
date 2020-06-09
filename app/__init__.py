from flask import Flask
from sqlalchemy import create_engine


app = Flask(__name__)
app.config['SECRET_KEY'] = 'you-will-never-guess'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:liner@localhost/rent_friends'

engine = create_engine('postgresql://postgres:liner@localhost/rent_friends')
conn = engine.connect()

from app import routes

