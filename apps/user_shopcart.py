#!/usr/bin/python3
from collections import OrderedDict
from uuid import uuid1
import dash
import json
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Event, State, Input, Output
from pprint import pprint
from app import app
from app import app_controller
import filestore
from utils import *
from dash.exceptions import PreventUpdate
from magic_defines import *
import json
from localstorage_writer import LocalStorageWriter
from localstorage_reader import LocalStorageReader

import coloredlogs, logging
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=logger)

def gen_id(name):
    # user module as name prefix
    s_id = g_id(__name__, name)
    return s_id

class ShoppingCart(object):
    def __init__(self, cart_info_str, controller):
        logger.debug(cart_info_str)
        self.cart_dict = None
        self.controller = controller
        self.cart_service = []
        try:
            logger.debug("loading cart_info_str")
            self.cart_dict = json.loads(cart_info_str)
        except:
            logger.debug("except happen")
            pass
        logger.debug("cart dict")
        logger.debug(self.cart_dict)
        if self.cart_dict:
            for s_id, quantity in self.cart_dict.items():
                service = self.controller.get_club_service(CLUB_NAME, s_id)
                if service and quantity > 0:
                    self.cart_service.append((quantity, service))

    def total_price(self):
        total = 0
        for item  in self.cart_service:
            quantity, service = item
            total += service.calc_price(quantity)
        return total

    def header(self):
        return html.Div(children=[
                    html.H3("Your Shopping Cart"),
                    html.Hr()
                ])

    def footer(self):
        return html.Div(className="container-fluid", children=[
            html.Div(className="row", children=[
                html.Div(className="col-12", children=[
                 html.Strong("Total {}".format(self.total_price()), className="float-right")
                ])
            ]),
            html.Div(className="row", children=[
                html.Div(className="col-7", children=[
                    dcc.Link(href="/service/list",
                             className="col btn btn-warning float-left ", children=[
                        html.I(className="fa fa-angle-left"),
                        S_CONTINUE_SHOP
                    ]),
                ]),
                html.Div(className="col", children=[
                    html.Button(id=gen_id(CHECKOUT),
                                className="btn btn-success btn-block float-right",
                                n_clicks=0,
                                children=[
                                    S_CHECKOUT,
                                    html.I(className="fa fa-angle-right")
                                ])
                ])
           ])
        ])

    def service_item(self, service, quantity):
        return  html.Div(className="cntainer-fluid border border-info", children = [
            html.Div(className="d-flex",children=[
                html.Div(className="p-2",children =[
                    html.Img(src=service.get_img_link(MAJOR_IMG),
                            width="100px",
                            height="100px",
                            alt=service.name,
                            className="img-responsive")
                ]),
                html.Div(className="p-2",children=[
                    html.H5(service.name,className="nomargin"),
                    html.P(service.description)
                ])
            ]),
            html.Div(className="d-flex justify-content-between",children=[
                html.Div(className="p-2", children=["price: {}*{}={}".format(service.price,
                                                                service.discount_percent_str(),
                                                                service.final_price())
                ]),
                html.Div(className="p-2", children=[
                    html.Span("Qty: "),
                    dcc.Input(type="numnber", value=quantity, size="10")
                ]),
            ]),
            html.Div(className="d-flex justify-content-between",children=[
                html.Div(className="p-2",children=[
                    html.Div(children=["Subtotal:",service.calc_price(quantity)]),
                ]),
                html.Div(className="p-2", children=[
                    html.Button(id=gen_id("del_service_{}".format(service.id)),
                                className="btn btn-danger btn-sm float-right",
                                children=[
                        html.I(className="fa fa-trash")
                    ])
                ])
            ])
        ])

    def all_cart_service(self, cart_service):
        item_list = []
        for item in cart_service:
            quantity, service = item
            item_list.append(self.service_item(service, quantity))
            item_list.append(html.Br())
        return item_list

    def body(self):
        return html.Div(children= self.all_cart_service(self.cart_service))

    def layout(self):
        return html.Div(id=gen_id(PLACEHOLDER), children = [
            self.header(),
            self.body(),
            html.Hr(),
            self.footer()
        ])

def layout(user_info, cart_info):
    logger.debug(user_info)
    logger.debug(cart_info)
    shop_cart = ShoppingCart(cart_info, app_controller)
    return html.Div(className="container", children=[
        LocalStorageWriter(id=gen_id(STORAGE_W), label=CART_STORAGE),
        LocalStorageReader(id=gen_id(STORAGE_R), label=CART_STORAGE),
        LocalStorageReader(id=gen_id(STORAGE_R2), label=USER_STORAGE),
        html.Div(id=gen_id(CART), className="container-fluid", children=[
            shop_cart.layout()
        ])
    ])




@app.callback(Output(gen_id(STORAGE_W), 'value'),
              [Input(gen_id(CHECKOUT), "n_clicks")],
              [State(gen_id(STORAGE_R), "value"),
               State(gen_id(STORAGE_R2), "value"),
               ])
def checkout(n_clicks, cart_info_str, jwt):
    assert_button_clicks(n_clicks)
    assert_has_value(jwt)
    shop_cart = ShoppingCart(cart_info_str, app_controller)
    order = app_controller.create_club_user_order(CLUB_NAME,
                                          jwt,
                                          shop_cart.cart_service)
    if order:
        return ""
    raise PreventUpdate()

