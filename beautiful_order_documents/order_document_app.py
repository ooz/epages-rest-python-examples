#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Author: Oliver Zscheyge
Description:
    Web app that generates beautiful order documents for ePages shops.
'''

import os
import sys

import epages
from flask import Flask, render_template, request, Response, abort, escape
import pdfkit

from dto import get_shop_logo, \
                get_orders, \
                get_order_views, \
                get_order_extended_pdf_str, \
                orders_to_table


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


@app.route('/')
def root():
    if has_private_app_credentials():
        return render_template('index.html', installed=True)
    return render_template('index.html', installed=False)

@app.route('/ui/orderlist')
def orderlist():
    try:
        logo_url =  get_shop_logo(CLIENT)
        orders = get_orders(CLIENT)
        ORDER_DB[ORDERS_FOR_MERCHANT_KEY] = orders_to_table(CLIENT, orders)
        orders = get_order_views(CLIENT, orders)
        return render_template('orderlist.html', orders=orders, logo=logo_url)
    except epages.RESTError, e:
        return \
u'''<h1>Something went wrong when fetching the order list! :(</h1>
<pre>
%s
</pre>
''' % escape(unicode(e)), 400

# Requires wkhtmltox or wkhtmltopdf installed besides Python's pdfkit
@app.route('/api/pdfs/<order_id>.pdf')
def pdf(order_id):
    orders_for_merchant = ORDER_DB.get(ORDERS_FOR_MERCHANT_KEY, {})
    if order_id in orders_for_merchant.keys():
        order = orders_for_merchant[order_id]
        filename = order_id + '.pdf'
        pdfkit.from_string(get_order_extended_pdf_str(CLIENT, order),
                           filename)
        pdffile = open(filename)
        response = Response(pdffile.read(), mimetype='application/pdf')
        pdffile.close()
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
    return '.ngrok.io' in url or \
           'localhost:8080' in url or \
           '0.0.0.0:80' in url

@app.errorhandler(404)
def page_not_found(e):
    return '<h1>404 File Not Found! :(</h1>', 404


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
    is_beyond = False
    if '--beyond' in sys.argv:
        is_beyond = True
    CLIENT_ID = os.environ.get('CLIENT_ID', '')
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET', '')
    API_URL = os.environ.get('API_URL', '')
    ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN', '')
    if is_beyond:
        CLIENT = epages.BYDClient(API_URL, CLIENT_ID, CLIENT_SECRET)
    else:
        CLIENT = epages.RESTClient(API_URL, ACCESS_TOKEN)
    SHOP_DB = {}
    CLIENT_DB = {}
    ORDER_DB = {}
    ORDERS_FOR_MERCHANT_KEY = API_URL + ACCESS_TOKEN
    assert has_client_credentials_or_private_app_credentials(), \
        'Please set either CLIENT_ID and CLIENT_SECRET or API_URL and ACCESS_TOKEN as environment variables!'

def has_client_credentials_or_private_app_credentials():
    return has_client_credentials() or \
           has_private_app_credentials()
def has_client_credentials():
    return CLIENT_ID != '' and CLIENT_SECRET != ''
def has_private_app_credentials():
    return API_URL != '' and ACCESS_TOKEN != ''


if __name__ == '__main__':
    init()
    app.run(host="0.0.0.0", port=80, threaded=True)
