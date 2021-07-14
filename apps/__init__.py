# @File        : __init__.py.py
# @Description :
# @Time        : 06 July, 2021
# @Author      : Cyan
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import settings

db = SQLAlchemy()


def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static', static_url_path='/')

    # set settings
    app.config.from_object(settings)

    # init db with app
    db.init_app(app)
    app.app_context().push()

    # register blueprint
    from apps.apis.apis import bp
    app.register_blueprint(bp)

    return app
