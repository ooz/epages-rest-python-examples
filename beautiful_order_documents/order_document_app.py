#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Author: Oliver Zscheyge
Description:
    Web app that generates beautiful order documents for ePages shops.
'''

import os

import epages
from flask import Flask, render_template, request, Response, abort
import pdfkit


app = Flask(__name__)

CLIENT_ID = ''
CLIENT_SECRET = ''
API_URL = ''
ACCESS_TOKEN = ''
CLIENT = None
SHOP_DB = {}
CLIENT_DB = {}
ORDER_DB = {}
ORDERS_FOR_MERCHANT_KEY = ''


def fetch_self_link(order):
    links = order.get('links', [])
    self_link = [link.get('href', '') for link in links if link.get("rel", "") == "self"][0]
    return self_link

def fetch_customer(order):
    try:
        links = order.get("links", [])
        customer_link = [link.get("href", "") for link in links if link.get("rel", "") == "customer"][0]
        if customer_link != "":
            customer = CLIENT.get(customer_link)
            billing_address = customer.get("billingAddress", {})
            return "%s %s" % (billing_address.get("firstName", ""), billing_address.get("lastName", ""))
    except epages.RESTError:
        pass
    return ""

class OrderViewData(object):
    def __init__(self, order):
        super(OrderViewData, self).__init__()
        self.order_number = order.get("orderNumber", "")
        self.pdf_link = "/api/pdfs/%s.pdf" % order.get("orderId", "")
        self.grand_total = "%s %s" % (order.get("grandTotal", ""), order.get("currencyId", ""))
        self.customer = fetch_customer(order)
        shop = {}
        try:
            shop = CLIENT.get("")
        except RESTError:
            pass
        self.logo_url = shop.get('logoUrl', '')
        self.shop_name = shop.get('name', '')
        self.shop_email = shop.get('email', '')
        billing_address = order.get('billingAddress', {})
        self.billing_name = billing_address.get('firstName', '') + " " + billing_address.get('lastName', '')
        self.billing_street = billing_address.get('street', '')
        self.billing_postcode = billing_address.get('zipCode', '')
        self.billing_town = billing_address.get('city', '')


    def __unicode__(self):
        return u"Order(%s, %s, %s)" % (self.order_number, self.customer, self.grand_total)

    def render_pdf(self):
        return render_template("order_document.html", order=self)

class OrderExtendedViewData(OrderViewData):
    """
    Does not just contain the order info, but also all line items.
    """
    def __init__(self, order):
        super(OrderExtendedViewData, self).__init__(order)
        self_link = fetch_self_link(order)
        print "Getting selflink: %s" % self_link
        order = {}
        try:
            order = CLIENT.get(self_link)
        except epages.RESTError, e:
            print "Error:"
            print unicode(e)
        line_item_container = order.get("lineItemContainer", {})
        product_line_items = line_item_container.get("productLineItems", [])
        self.products = [ProductViewData(product) for product in product_line_items]

class ProductViewData(object):
    def __init__(self, product):
        super(ProductViewData, self).__init__()
        self.name = product.get('name', '')
        self.quantity = "1"
        self.tax = "2"
        self.price_per_item = "3"
        self.price_total = "4"

    def __unicode__(self):
        return u"Product()"


@app.route('/')
def root():
    if has_private_app_credentials():
        return render_template('index.html', installed=True)
    return render_template('index.html', installed=False)

@app.route('/ui/orderlist')
def orderlist():
    try:
        logo_url = CLIENT.get("").get("logoUrl", "")
        orders_response = CLIENT.get("/orders")
        orders = orders_response.get("items", [])
        order_table = {}
        for order in orders:
            order_table[order["orderId"]] = order
        ORDER_DB[ORDERS_FOR_MERCHANT_KEY] = order_table
        orders = [OrderViewData(order) for order in orders]
        return render_template("orderlist.html", orders=orders, logo=logo_url)
    except:
        return 'Something went wrong when fetching the order list! :(', 400

# Requires wkhtmltox or wkhtmltopdf installed besides Python's pdfkit
@app.route('/api/pdfs/<order_id>.pdf')
def pdf(order_id):
    orders_for_merchant = ORDER_DB.get(ORDERS_FOR_MERCHANT_KEY, {})
    if order_id in orders_for_merchant.keys():
        order = orders_for_merchant[order_id]
        filename = order_id + ".pdf"
        pdfkit.from_string(OrderExtendedViewData(order).render_pdf(), filename)
        pdf = open(filename)
        response = Response(pdf.read(), mimetype='application/pdf')
        pdf.close()
        os.remove(filename)
        return response
    abort(404)


@app.before_request
def limit_open_proxy_requests():
    '''Security measure to prevent:
    http://serverfault.com/questions/530867/baidu-in-nginx-access-log
    http://security.stackexchange.com/questions/41078/url-from-another-domain-in-my-access-log
    http://serverfault.com/questions/115827/why-does-apache-log-requests-to-get-http-www-google-com-with-code-200
    http://stackoverflow.com/questions/22251038/how-to-limit-flask-dev-server-to-only-one-visiting-ip-address
    '''
    if not is_allowed_request():
        print request.url_root
        print request
        abort(403)

def is_allowed_request():
    url = request.url_root
    return ".ngrok.io" in url or \
           "localhost:8080" in url or \
           "0.0.0.0:80" in url

@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404 File Not Found! :(</h1>", 404


def init():
    global CLIENT_ID
    global CLIENT_SECRET
    global API_URL
    global ACCESS_TOKEN
    global CLIENT
    global SHOP_DB
    global CLIENT_DB
    global ORDER_DB
    global ORDERS_FOR_MERCHANT_KEY
    CLIENT_ID = os.environ.get('CLIENT_ID', '')
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET', '')
    API_URL = os.environ.get('API_URL', '')
    ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN', '')
    CLIENT = epages.RESTClient(API_URL, ACCESS_TOKEN)
    SHOP_DB = {}
    CLIENT_DB = {}
    ORDER_DB = {}
    ORDERS_FOR_MERCHANT_KEY = API_URL + ACCESS_TOKEN
    assert has_client_credentials_or_private_app_credentials(), \
        'Please set either CLIENT_ID and CLIENT_SECRET or API_URL and ACCESS_TOKEN as environment variables!'

def has_client_credentials_or_private_app_credentials():
    return has_client_credentials() or has_private_app_credentials()
def has_client_credentials():
    return CLIENT_ID != '' and CLIENT_SECRET != ''
def has_private_app_credentials():
    return API_URL != '' and ACCESS_TOKEN != ''

if __name__ == '__main__':
    init()
    app.run(host="0.0.0.0", port=80, threaded=True)
