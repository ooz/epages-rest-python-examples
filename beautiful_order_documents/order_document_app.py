#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Author: Oliver Zscheyge
Description:
    Web app that generates beautiful order documents for ePages shops.
'''

from flask import Flask, render_template, Response, abort
import os
import pdfkit

import epages

app = Flask(__name__)

API_URL = os.environ.get('EPAGES_API_URL', '')
ACCESS_TOKEN = os.environ.get('EPAGES_TOKEN', '')
CLIENT = epages.HTTPClient(API_URL, ACCESS_TOKEN)
ORDERS_DB = {}
ORDERS_FOR_MERCHANT_KEY = API_URL + ACCESS_TOKEN

def fetch_self_link(order):
    links = order.get("links", [])
    self_link = [link.get("href", "") for link in links if link.get("rel", "") == "self"][0]
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
        self.pdf_link = "pdf/%s.pdf" % order.get("orderId", "")
        self.grand_total = "%s %s" % (order.get("grandTotal", ""), order.get("currencyId", ""))
        self.customer = fetch_customer(order)
        self.logo_url = ""
        try:
            self.logo_url = CLIENT.get("").get("logoUrl", "")
        except RESTError:
            pass
        self.billing_name = "billing_name"
        self.billing_street = "billing_street"
        self.billing_postcode = "billing_postcode"
        self.billing_town = "billing_town"
        self.shop_name = "shop_name"
        self.shop_street = "shop_street"
        self.shop_postcode = "shop_postcode"
        self.shop_town = "shop_town"
        self.invoice_number = "1337"

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
        order = CLIENT.get(self_link)
        line_item_container = order.get("lineItemContainer", {})
        product_line_items = line_item_container.get("productLineItems", [])
        self.products = [ProductViewData(product) for product in product_line_items]

class ProductViewData(object):
    def __init__(self, product):
        super(ProductViewData, self).__init__()
        self.name = product.get("name", "")
        self.quantity = "1"
        self.tax = "2"
        self.price_per_item = "3"
        self.price_total = "4"

    def __unicode__(self):
        return u"Product()"


@app.route('/')
def root():
    try:
        logo_url = CLIENT.get("").get("logoUrl", "")
        orders_response = CLIENT.get("/orders")
        orders = orders_response.get("items", [])
        order_table = {}
        for order in orders:
            order_table[order["orderId"]] = order
        ORDERS_DB[ORDERS_FOR_MERCHANT_KEY] = order_table
        orders = [OrderViewData(order) for order in orders]
        return render_template("orderlist.html", orders=orders, logo=logo_url)
    except:
        return unicode('Something went wrong! :(')

# Requires wkhtmltox or wkhtmltopdf installed besides Python's pdfkit
@app.route('/pdf/<order_id>.pdf')
def pdf(order_id):
    orders_for_merchant = ORDERS_DB.get(ORDERS_FOR_MERCHANT_KEY, {})
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

@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404 File Not Found! :(</h1>", 404

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, threaded=True)
