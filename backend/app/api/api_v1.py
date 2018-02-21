#!/usr/bin/python

from flask_restplus import Namespace, Resource, fields
from flask import abort, request, send_from_directory
from werkzeug import secure_filename
from utils import *
from . import app_controller

api = Namespace('api_v1', description='API version 1')

def get_payload():
    return api.apis[0].payload

def raise_error(resp_except):
    abort(resp_except.http_code, resp_except.message)


user_model = api.model('User', {
    'email': fields.String(required=True, description="user's email"),
    'tel': fields.String(description="user's telephone number"),
    'roles':fields.List(fields.String, description="user roles"),
    'password':fields.String(required=False, description= "user's password")
})

@api.route('/<club_name>/user')
class UserList(Resource):
    @api.doc('List all users')
    @api.marshal_list_with(user_model)
    def get(self, club_name):
        try:
            return app_controller.get_club_user_list(club_name)
        except RespExcept as e:
            raise_error(e)

    @api.expect(user_model)
    @api.marshal_with(user_model)
    def post(self, club_name):
        try:
            return app_controller.create_club_user(club_name, get_payload())
        except RespExcept as e:
            raise_error(e)

@api.route('/<club_name>/user/<user_email>')
@api.param('club_name', 'the name of a club')
@api.param('user_email', "The user email")
@api.response(404, 'user not found')
class User(Resource):
    @api.doc('get one user information')
    @api.marshal_with(user_model)
    def get(self, club_name, user_email):
        return app_controller.get_club_user_by_email(club_name, user_email)

    @api.expect(user_model)
    @api.marshal_with(user_model)
    def put(self, club_name, user_email):
        return app_controller.update_user(club_name, user_email, get_payload())

    def delete(self, club_name, user_email):
        return app_controller.delete_club_user_by_email(club_name, user_email)

club_model = api.model('club', {
    'name': fields.String(required=True, description="user's email"),
    'description': fields.String(required=True, description="user's email"),
})

@api.route('/club')
class ClubList(Resource):
    @api.doc('List all clubs')
    @api.marshal_list_with(club_model)
    def get(self):
        try:
            return app_controller.get_club_list()
        except RespExcept as e:
            raise_error(e)

    @api.expect(club_model)
    @api.marshal_with(club_model)
    def post(self):
        try:
            return app_controller.create_club(get_payload())
        except RespExcept as e:
            raise_error(e)

@api.route('/club/<club_name>')
@api.param('club_name', 'the name of a club')
@api.response(404, 'club not found')
class Club(Resource):
    @api.doc('get one club information')
    @api.marshal_with(club_model)
    def get(self, club_name):
        try:
            return app_controller.get_club_by_name(club_name)
        except RespExcept as e:
            raise_error(e)

    def delete(self, club_name):
        try:
            return app_controller.delete_club_by_name(club_name)
        except RespExcept as e:
            raise_error(e)

    @api.expect(club_model)
    @api.marshal_with(club_model)
    def put(self, club_name):
        try:
            return app_controller.update_club(club_name, get_payload())
        except RespExcept as e:
            raise_error(e)

role_model = api.model('role', {
    'name': fields.String(required=True, description="user's email"),
    'description': fields.String(description="descripion of a role"),
})
@api.route('/<club_name>/role')
class RoleList(Resource):
    @api.doc('List all roles')
    @api.marshal_list_with(role_model)
    def get(self, club_name):
        return app_controller.get_club_role_list(club_name)

    @api.expect(role_model)
    @api.marshal_with(role_model)
    def post(self, club_name):
        return app_controller.create_club_role(club_name, get_payload())

@api.route('/<club_name>/role/<role_name>')
@api.param('club_name', 'the name of a club')
@api.response(404, 'club not found')
class Role(Resource):
    @api.doc('get one role')
    @api.marshal_with(role_model)
    def get(self, club_name, role_name):
        return app_controller.get_club_role_by_name(club_name, role_name)

    def delete(self, club_name, role_name):
        return app_controller.delete_club_role_by_name(club_name, role_name)
    
    @api.expect(club_model)
    @api.marshal_with(club_model)
    def put(self, club_name, role_name):
        return app_controller.update_club_role(club_name, role_name, get_payload())

service_model = api.model('service', {
    'id': fields.Integer(required=True),
    'name': fields.String(required=True),
    'description':fields.String(required=True),
    'price': fields.Integer(required=True),
    'discount': fields.Integer(required=True),
    'major_pic': fields.Integer(required=True), 
    'pic_and_text' : fields.List(fields.String),
    'active': fields.Boolean() 
})
@api.route('/<club_name>/service')
class ServiceList(Resource):
    @api.doc('List club services')
    @api.marshal_list_with(role_model)
    def get(self, club_name):
        return app_controller.get_club_service_list(club_name)

    @api.expect(role_model)
    @api.marshal_with(role_model)
    def post(self):
        return app_controller.create_club_service(club_name, get_payload())

@api.route('/<club_name>/service/<service_name>')
@api.param('club_name', 'the name of a club')
@api.response(404, 'club not found')
class Service(Resource):
    @api.doc('get one club service detail')
    @api.marshal_with(role_model)
    def get(self, club_name, service_name):
        return app_controller.get_club_service_by_name(club_name, service_name)

    def delete(self, club_name, service_name):
        return app_controller.delete_club_service_by_name(club_name, service_name)
    
    @api.expect(club_model)
    @api.marshal_with(club_model)
    def put(self, club_name, service_name):
        return app_controller.update_club_service(club_name, service_name, get_payload())




url_model= api.model('url_model', {
    'url': fields.String(required=True, description="url to upload or download"),
})

@api.route('/filestore/service/<id>/<filename>')
class ServiceFileDownload(Resource):
    def get(self, id, filename):
        return send_from_directory(app_controller.get_filestore_service(id), filename)

@api.route('/FileStore/service/<id>')
class ServiceFileUpload(Resource):
    @api.marshal_list_with(url_model)
    def post(self, id):
        # Get the name of the uploaded files
        uploaded_files = request.files.getlist("file[]")
        filenames = []
        for file in uploaded_files and app_controller.allow_file(file.filename):
            # Make the filename safe, remove unsupported chars
            filename = secure_filename(file.filename)
            # Move the file form the temporal folder to the upload
            # folder we setup
            file_path = os.path.join(app_controller.get_filestore_service(id), filename)
            file.save(file_path)
            # Save the filename into a list, we'll use it later
            filenames.append("/filestore/service/" + id + "/" + filename)