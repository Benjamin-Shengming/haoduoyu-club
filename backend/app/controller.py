#!/usr/bin/python

from flask import Blueprint, render_template, abort 
from jinja2 import TemplateNotFound
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from .models import AppModel 
from werkzeug.security import generate_password_hash, check_password_hash

from .models import AppModel
from json import loads

from utils import caller_info 
import coloredlogs, logging
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=logger)

class AppController(object):
    def __init__(self):
        self.db_model = AppModel()

    # club related functions
    def get_club_list(self):
        user_list = self.db_model.get_club_list()
        return user_list 

    def create_club(self, club_data):
        club = self.db_model.create_club(club_data)
        return  club

    def delete_club_by_name(self, club_name):
        return self.db_model.delete_club_by_name(club_name)
        
    def update_club(self, club_name, club_data):
        club = self.db_model.update_club(club_name, club_data)
        return club

    def get_club_by_name(self, club_name):
        return self.db_model.get_club_by_name(club_name)

    # user related functions
    def get_user_by_id(self, user_id):
        return self.db_model.get_user_by_id(user_id)

    def get_club_user_list(self, club_name):
        user_list = self.db_model.get_club_user_list(club_name)
        return user_list

    def create_club_user(self, club_name, user_data):
        if not user_data.get('roles', None): 
            # by default, the role is user
            user_data['roles'] = ['user']
        new_user = self.db_model.create_club_user(club_name ,user_data)
        return new_user 

    def get_club_user_by_email(self, club_name, user_email):
        user = self.db_model.get_club_user_by_email(club_name, user_email)
        return  user

    def verify_club_user(self, club_name, user_data):
        user = self.db_model.verify_club_user(club_name, user_data)
        return  user

    def delete_club_user_by_email(self, club_name, user_email):
        return self.db_model.delete_club_user(club_name, user_email)
    
    def update_club_user(self, club_name, user_email, user_data):
        return self.update_club_user(club_name, user_email, user_data)

    # role realted functions
    def get_club_role_list(self, club_name):
        return self.db_model.get_club_role_list(club_name)

    def get_club_role(self, club_name, role_name):
        return self.db_model.get_club_role_by_name(club_name, role_name)

    def create_club_role(self, club_name, role_data):
        return self.db_model.create_club_role(club_name, role_data)
    
    def update_club_role(self, club_name, role_name, role_data):
        return self.db_model.update_club_role(club_name, role_name, role_data)

    def delete_club_role_by_name(self, club_name, role_name):
        return self.db_model.delete_club_role_by_name(club_name, role_name)

    def get_filestore_dir(self):
        return self.db_model.get_filestore_dir()

    def get_filestore_service(self, id):
        return self.db_model.get_filestore_service(id)

    def allow_file(self, filename):
      allow_ext = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
      return '.' in filename and filename.rsplit('.', 1)[1] in allow_ext 