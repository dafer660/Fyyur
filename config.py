import os
import sys
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database
# hard coded the username+password for dev only.
# there should be a variable for os variable like:
# os.environ.get('DATABASE_URL') or etc...
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost/Fyyur'
SQLALCHEMY_TRACK_MODIFICATIONS = False
