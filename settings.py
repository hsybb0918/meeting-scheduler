# @File        : settings.py
# @Description :
# @Time        : 07 July, 2021
# @Author      : Cyan

ENV = 'development'
DEBUG = True

SQLALCHEMY_DATABASE_URI = 'sqlite:///mams.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

BUNDLE_ERRORS = True
