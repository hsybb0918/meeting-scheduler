# @File        : settings.py
# @Description :
# @Time        : 07 July, 2021
# @Author      : Cyan

# for flask environment
ENV = 'development'
DEBUG = True

# for flask-sqlalchemy
SQLALCHEMY_DATABASE_URI = 'sqlite:///mams.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# for flask-restful
BUNDLE_ERRORS = True
