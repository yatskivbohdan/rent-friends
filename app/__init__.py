from flask import Flask
from sqlalchemy import create_engine


app = Flask(__name__)
app.config['SECRET_KEY'] = 'you_never_guess'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://team7:passw7ord@142.93.163.88:6006/db7'

engine = create_engine('postgresql://team7:passw7ord@142.93.163.88:6006/db7')
conn = engine.connect()

from app import routes

