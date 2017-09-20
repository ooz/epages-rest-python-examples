# -*- coding: utf-8 -*-

import epages
from flask import render_template


def get_orders(client):
    orders_response = client.get('/orders')
    return orders_response.get('items', [])

def get_order_views(client, orders):
    return [OrderViewData(order, client) for order in orders]

def get_order_extended_pdf_str(client, order):
    return OrderExtendedViewData(order, client).render_pdf()

def get_shop_logo(client):
    return client.get('').get('logoUrl', '')

def orders_to_table(client, orders):
    order_table = {}
    for order in orders:
        if client.beyond:
            pass
        else:
            order_table[order['orderId']] = order
    return order_table


class OrderViewData(object):
    def __init__(self, order, client):
        super(OrderViewData, self).__init__()
        self.client = client
        self.order_number = order.get('orderNumber', '')
        self.pdf_link = '/api/pdfs/%s.pdf' % order.get('orderId', '')
        self.grand_total = '%s %s' % (order.get('grandTotal', ''), order.get('currencyId', ''))
        self.customer = self._fetch_customer(order)
        shop = {}
        try:
            shop = self.client.get('')
        except epages.RESTError:
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
        return u'Order(%s, %s, %s)' % (self.order_number, self.customer, self.grand_total)

    def render_pdf(self):
        return render_template('order_document.html', order=self)

    def _fetch_customer(self, order):
        try:
            links = order.get('links', [])
            customer_link = [link.get('href', '') for link \
                                                  in links \
                                                  if link.get('rel', '') == 'customer'][0]
            if customer_link != '':
                customer = self.client.get(customer_link)
                billing_address = customer.get('billingAddress', {})
                return '%s %s' % (billing_address.get('firstName', ''), billing_address.get('lastName', ''))
        except epages.RESTError:
            pass
        return u''

class OrderExtendedViewData(OrderViewData):
    '''
    Does not just contain the order info, but also all line items.
    '''
    def __init__(self, order, client):
        super(OrderExtendedViewData, self).__init__(order, client)
        self_link = self._fetch_self_link(order)
        order = {}
        try:
            order = self.client.get(self_link)
        except epages.RESTError:
            pass
        line_item_container = order.get('lineItemContainer', {})
        product_line_items = line_item_container.get('productLineItems', [])
        self.shipping_total = order.get('shippingData', {}).get('price', {}).get('formatted', None)
        self.products = [ProductViewData(product) for product in product_line_items]

    def _fetch_self_link(self, order):
        links = order.get('links', [])
        self_link = [link.get('href', '') for link in links if link.get('rel', '') == 'self'][0]
        return self_link

class ProductViewData(object):
    def __init__(self, product):
        super(ProductViewData, self).__init__()
        self.name = product.get('name', '')
        self.quantity = product.get('quantity', {}).get('amount', '')
        self.tax = unicode(product.get('taxClass', {}).get('percentage', '')).replace('.0', '') + ' %'
        self.price_per_item = product.get('singleItemPrice', {}).get('formatted', '')
        self.price_total = product.get('lineItemPrice', {}).get('formatted', '')
        self.icon = None
        icons = [img for img in product.get('images', []) if img.get('classifier', '') == 'Thumbnail']
        if icons:
            self.icon = icons[0].get('url', None)

    def __unicode__(self):
        return u'Product()'
