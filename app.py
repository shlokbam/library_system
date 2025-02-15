# app.py
from flask import Flask
import os
from dotenv import load_dotenv
import pymysql
from extensions import db, login_manager
from models import User  # Add this import at the top
from flask_mail import Mail
from email_service import mail, send_welcome_email

pymysql.install_as_MySQLdb()
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure app
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DB')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Initialize extensions
mail.init_app(app)
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

# Add the user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Import routes after initializing extensions
from routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)