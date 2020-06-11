from flask import Flask, render_template, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'b32480029a0205f8e3fd840066627a11638b3eecf5a8c7910b4a39ff7b1a830c'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///websitedb.db'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from Blog import routes