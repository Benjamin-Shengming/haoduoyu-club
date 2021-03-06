#!/usr/bin/python
from random import randint
from models import AppModel
import coloredlogs
import logging
from datetime import datetime, timedelta
import jwt
from utils import RespExcept, is_tel, is_email
from email_smtp import EmailClientSMTP
import filestore
import gettext
from mobile_msg import CebMobileMsg
from utils import LoginExpireMsg
from magic_defines import (JWT_ALGORITHM, JWT_EXP_DELTA_HOURS, JWT_SECRET_KEY,
                           MAJOR_IMG, S_CLUBNAME, CLUB_NAME, locale_d
                           )

logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=logger)

zh = gettext.translation("controller", locale_d(), languages=["zh_CN"])
zh.install(True)
_ = zh.gettext


class AppController(object):
    def __init__(self):
        self.db_model = AppModel()

    def save(self, obj):
        self.db_model.save(obj)

    # club related functions
    def get_club_list(self):
        user_list = self.db_model.get_club_list()
        return user_list

    def create_club(self, club_data):
        club = self.db_model.create_club(club_data)
        return club

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

    def _decode_user_jwt(self, encoded_jwt):
        payload = jwt.decode(encoded_jwt.encode('UTF-8'),
                             JWT_SECRET_KEY,
                             JWT_ALGORITHM)
        return payload

    def get_club_user_by_tel_or_email(self, club_name, tel_email):
        if is_tel(tel_email):
            return self.get_club_user_by_tel(club_name, tel_email)
        elif is_email(tel_email):
            return self.get_club_user_by_email(club_name, tel_email)
        return None

    def get_club_user_by_jwt(self, club_name, encoded_jwt):
        u = None
        try:
            user_dict = self._decode_user_jwt(encoded_jwt)
            u = self.get_club_user_by_id(club_name, user_dict['user_id'])
        except Exception as e:
            logger.debug(str(e))

        return u

    def generate_user_jwt(self, club_name, user):
        payload = {
            'user_id': user.id,
            'club_name': club_name,
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXP_DELTA_HOURS)
        }
        jwt_token = jwt.encode(payload, JWT_SECRET_KEY, JWT_ALGORITHM)
        return jwt_token.decode(encoding='UTF-8')

    def activate_club_user_by_jwt(self, club_name, encoded_jwt, code):
        user = self.get_club_user_by_jwt(club_name, encoded_jwt)
        if not user:
            raise LoginExpireMsg()
        user.activate(code)
        self.db_model.save(user)

    def activate_club_user_by_email(self, club_name, email, activate_code):
        '''
        confirm_serializer = URLSafeTimedSerializer(SECRET_KEY)
        email = confirm_serializer.loads(token, salt=EMAIL_SALT, max_age=36000)
        '''
        user = self.get_club_user_by_email(club_name, email)
        user.activate(activate_code)
        if user.activate_code == activate_code:
            user.email_confirmed = True
            self.db_model._add_commit(user)
        else:
            raise RespExcept("Activation code is not right!")
        return user

    def resend_activate_code_by_tel(self, club_name, mobile):
        logger.debug("send activated code by tel")
        logger.debug(mobile)
        user = self.db_model.get_club_user_by_tel(club_name, mobile)
        if not user:
            raise RespExcept("User does not exist")
        code = self.generate_club_user_activate_code(club_name, user)
        content = _("{} activation code is: {}").format(S_CLUBNAME, code)
        CebMobileMsg().send(mobile, content)

    def resend_activate_code_by_email(self, club_name, email_address):
        logger.debug("club_name")
        logger.debug(email_address)
        user = self.db_model.get_club_user_by_email(club_name, email_address)
        if not user:
            raise RespExcept("User does not exist")
        if user.email_confirmed:
            raise RespExcept("user already activated!")
        code = self.generate_club_user_activate_code(club_name, user)
        club = user.club
        email_body = _("Your activation code is {}").format(code)
        EmailClientSMTP(club.smtp_server,
                        club.smtp_port,
                        club.smtp_encryption,
                        club.email,
                        club.email_pwd).send_email(
                            user.email,
                            subject=_("activate account"),
                            body=email_body)

    def generate_club_user_activate_code(self, club_name, user):
        code = ""
        length = 5
        for i in range(0, length):
            code += str(randint(0, 9))
        logger.debug(code)
        user.activate_code = code
        self.db_model._add_commit(user)
        return code
        '''
        confirm_serializer = URLSafeTimedSerializer(SECRET_KEY)
        token = confirm_serializer.dumps(user.email, salt=EMAIL_SALT)
        return ("/{}/email/activate/{}".format(club_name, token))
        '''

    def create_club_user(self, club_name, user_data):
        logger.debug(user_data)
        if not user_data.get('roles', None):
            # by default, the role is user
            user_data['roles'] = ['user']
        new_user = self.db_model.create_club_user(club_name, user_data)
        return new_user

    def get_club_user_by_id(self, club_name, user_id):
        user = self.db_model.get_club_user_by_id(club_name, user_id)
        return user

    def get_club_user_by_email(self, club_name, user_email):
        user = self.db_model.get_club_user_by_email(club_name, user_email)
        return user

    def get_club_user_by_tel(self, club_name, user_tel):
        user = self.db_model.get_club_user_by_tel(club_name, user_tel)
        return user

    def get_club_user_by_email_or_tel(self, club_name, tel_or_email):
        return self.db_model.get_club_user_by_email_or_tel(club_name,
                                                           tel_or_email)

    def verify_club_user(self, club_name, user_data):
        user = self.db_model.verify_club_user(club_name, user_data)
        return user

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

    def allow_file(self, filename):
        allow_ext = set(['txt', 'png', 'jpg', 'jpeg', 'gif'])
        return '.' in filename and filename.rsplit('.', 1)[1] in allow_ext

    def _save_service_files(self,
                            service_id,
                            major_img,
                            img_list,
                            txt_list):
        filestore.save_service_img(service_id, MAJOR_IMG, major_img)
        # save all other imgs
        for i, img_content in enumerate(img_list):
            filestore.save_service_img(service_id, i, img_content)

        # save txt to file
        for i, txt_content in enumerate(txt_list):
            filestore.save_service_txt(service_id, i, txt_content)

    # service related functions
    def create_club_service(self,
                            club_name,
                            service_data,
                            major_img,
                            img_list,
                            txt_list):
        logger.debug(service_data)
        service_id = service_data["id"]
        self._save_service_files(service_id, major_img, img_list, txt_list)
        return self.db_model.create_club_service(club_name, service_data)

    def update_club_service(self,
                            club_name,
                            service_id,
                            service_data,
                            major_img,
                            img_list,
                            txt_list):

        self._save_service_files(service_id, major_img, img_list, txt_list)
        return self.db_model.update_club_service(club_name,
                                                 service_id,
                                                 service_data)

    def get_club_service_list(self, club_name):
        logger.debug(club_name)
        return self.db_model.get_club_service_list(club_name)

    def get_club_service(self, club_name, service_id):
        return self.db_model.get_club_service(club_name, service_id)

    def get_club_service_by_name(self, club_name, service_name):
        return self.db_model.get_club_service_by_name(club_name, service_name)

    def get_club_headline_service(self, club_name):
        return self.db_model.get_club_headline_service(club_name)

    def get_club_top_one_service_id(self, club_name):
        services = self.db_model.get_club_headline_service(club_name)
        if services:
            return services[0].id

        service = self.get_club_service_list(CLUB_NAME)
        return service[0].id

    def get_club_service_paginate_date(self, club_name, start, numbers=20):
        return self.db_model.get_club_service_paginate_date(club_name,
                                                            start,
                                                            numbers)

    def delete_club_service(self, club_name, service_id):
        return self.db_model.delete_club_service(club_name, service_id)

    def create_club_user_order(self, club_name, jwt, quantity_service):
        if len(quantity_service) <= 0:
            return
        user = self.get_club_user_by_jwt(club_name, jwt)
        order = self.db_model.create_club_user_order(club_name,
                                                     user,
                                                     quantity_service)
        if order:
            self.save(order)
        return order

    def get_club_order_by_id(self, order_id):
        return self.db_model.get_order_by_id(order_id)

    def get_club_order_list(self, club_name):
        return self.db_model.get_club_order_list(club_name)

    # check one service has special keywords

    def _service_has_keyword(self, service, key_words):
        # check name
        for key in key_words:
            if key in service.name:
                return True
        # check description
        for key in key_words:
            if key in service.description:
                return True
        return False

    def service_to_article(self, service, club_name):
        article = {}
        article['title'] = service.name
        article['description'] = service.description
        article['image'] = filestore.get_service_img_link(service.id,
                                                          MAJOR_IMG)
        article['url'] = "/service/book/{}".format(service.id)
        return article

    def search_club_service_article(self, club_name, key_words):
        # given a set of keywords and search the service contains the key word
        # if keyword is empty, just return most important
        services = self.get_club_service_list(club_name)
        ret = [item for item in services
               if self._service_has_keyword(item, key_words)]
        if not ret:
            ret = services[:min(5, len(services))]
        return [self.service_to_article(item, club_name) for item in ret]

    def create_remote_ip_activity(self, ip_addr):
        self.db_model.create_ip_activity(ip_addr)

    def get_remote_ip_activity(self):
        return self.db_model.search_ip_activity()

    def resend_user_otp(self, user):
        if not user.has_otp() or user.is_otp_expire():
            user.generate_otp()
            self.db_model.save(user)
            content = _("Your one time password is {}").format(user.otp)
            CebMobileMsg().send(user.tel, content)
