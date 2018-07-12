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
        return html.Thead(
                    html.Tr(children=[
                        html.Th("Product",style={"width":"50%"}),
                        html.Th("Price", style={"width":"10%"}),
                        html.Th("Quantity", style={"width":"8%"}),
                        html.Th("Subtotal", style={"width":"22%"}, className="text-center"),
                        html.Th(style={"width":"10%"})
                    ])
                )

    def footer(self):
        return html.Tfoot(children=[
            html.Tr(children=[
                html.Td(children=[
                    dcc.Link(href="/service/list", className="btn btn-warning", children=[
                        html.I(className="fa fa-angle-left"),
                        S_CONTINUE_SHOP
                    ])
                ]),
                html.Td(className="hidden-xs"),
                html.Td(className="hidden-xs text-center", children=[
                    html.Strong("Total {}".format(self.total_price()))
                ]),
                html.Td(children=[
                    html.Button(id=gen_id(CHECKOUT),
                                className="btn btn-success btn-block",
                                n_clicks=0,
                                children=[
                                    S_CHECKOUT,
                                    html.I(className="fa fa-angle-right")
                                ])
                ])
            ])
        ])

    def service_del_button(self, sid):
        return html.Td(className="actions", children=[
            html.Button(id=gen_id("del_service_{}".format(sid)),
                        className="btn btn-danger btn-sm", children=[
                html.I(className="fa fa-trash")
            ])
        ])

    def service_item(self, service, quantity):
        return html.Tr(children=[
            html.Td(**{"data-th": "Product"}, children=[
            html.Div(className="row", children=[
                html.Div(className="col-sm-2 hidden-xs", children =[
                    html.Img(src=service.get_img_link(MAJOR_IMG),
                            width="100px",
                            height="100px",
                            alt=service.name,
                            className="img-responsive")
                ]),
                html.Div(className="col-sm-1 hidden-xs", children =[""]),
                html.Div(className="col-sm-9", children=[
                html.H4(service.name,className="nomargin"),
                html.P(service.description)
                ])
            ])
            ]),
            html.Td(**{"data-th":"Price"}, children=["{}*{}={}".format(service.price,
                                                            service.discount_percent_str(),
                                                            service.final_price())]),
            html.Td(**{"data-th":"Quantity"}, children=[
            dcc.Input(type="number",
                        className="form-control text-center",
                        value=quantity)

            ]),
            html.Td(**{"data-th":"Subtotal"}, className="text-center", children=[service.calc_price(quantity)]),
            self.service_del_button(service.id)
        ])

    def all_cart_service(self, cart_service):
        item_list = []
        for item in cart_service:
            quantity, service = item
            item_list.append(self.service_item(service, quantity))
        return item_list

    def body(self):
        return html.Tbody(children= self.all_cart_service(self.cart_service))

    def layout(self):
        return html.Div(id=gen_id(PLACEHOLDER), children = [
            self.header(),
            self.body(),
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
        html.Table(id=gen_id(CART), className="table table-hover table-condensed", children=[
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

