#!/usr/bin/python
import os 
import sys
from flask import Flask
from flask_restplus import Api, Resource, fields
from werkzeug.contrib.fixers import ProxyFix
from flask_restplus import Api, cors
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_babel import Babel 


app = Flask(__name__,
            static_folder = "../../dist/static",
            template_folder = "../../dist")
app.wsgi_app = ProxyFix(app.wsgi_app)


app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
app.config['BABEL_DEFAULT_LOCALE'] = 'zh_Hans_CN'
app.config['UPLOAD_FOLDER'] = 'filestore/'
app.config['CORS_HEADERS'] = 'Content-Type'

api_interface = Api(
    title='backend support system',
    version='1.0',
    description='this backend system will support all clubs',
    doc='/swagger/'
)
api_interface.decorators=[cors.crossdomain(origin="*")]

babel = Babel(app)

# create controller object, the central point 
from .controller import AppController
app_controller = AppController()
from .api import ns1
#from .views import  view_pages

api_interface.add_namespace(ns1, path='/api_v1')
api_interface.init_app(app)
