# -*- coding: utf-8 -*-

import re

import epages
from flask import render_template, escape


def get_orders(client):
    orders_response = client.get('/orders')
    if client.beyond:
        return orders_response.get('_embedded', {}).get('orders', [])
    return orders_response.get('items', [])

def get_order_views(client, orders):
    if client.beyond:
        return [BydOrderViewData(order, client) for order in orders]
    return [OrderViewData(order, client) for order in orders]

def get_order_extended_pdf_str(client, order):
    if client.beyond:
        return BydOrderExtendedViewData(order, client).render_pdf()
    return OrderExtendedViewData(order, client).render_pdf()

def get_shop_logo(client):
    if client.beyond:
        return _get_byd_shop_logo(client)
    return client.get('').get('logoUrl', '')

def _get_byd_shop_logo(client):
    shop_images = {}
    try:
        shop_images = client.get('/shop/images')
    except epages.RESTError, error:
        print unicode(error)
    shop_images = [img for img \
                        in shop_images.get('_embedded', {}).get('images', []) \
                        if img.get('label', '') == 'logo']
    logo_url = ''
    if shop_images:
        logo_url = shop_images[0].get('_links', {}).get('data', {}).get('href', '')
    # Hack to remove image link template params
    logo_url = re.sub(r'\{.*\}', '', logo_url)
    logo_url += '&height=128'
    return logo_url

def orders_to_table(client, orders):
    order_table = {}
    for order in orders:
        if client.beyond:
            order_table[order['_id']] = order
        else:
            order_table[order['orderId']] = order
    return order_table


class OrderViewData(object):
    def __init__(self, order, client):
        super(OrderViewData, self).__init__()
        self.client = client
        self.order_number = escape(order.get('orderNumber', ''))
        self.pdf_link = '/api/pdfs/%s.pdf' % order.get('orderId', '')
        self.grand_total = '%s %s' % (order.get('grandTotal', ''), order.get('currencyId', ''))
        self.customer = escape(self._fetch_customer(order))
        shop = {}
        try:
            shop = self.client.get('')
        except epages.RESTError:
            pass
        self.logo_url = shop.get('logoUrl', '')
        self.shop_name = escape(shop.get('name', ''))
        self.shop_email = shop.get('email', '')
        billing_address = order.get('billingAddress', {})
        self.billing_name = escape(billing_address.get('firstName', '') + ' ' + \
                                   billing_address.get('lastName', ''))
        self.billing_street = escape(billing_address.get('street', ''))
        self.billing_postcode = escape(billing_address.get('zipCode', ''))
        self.billing_town = escape(billing_address.get('city', ''))

    def __unicode__(self):
        return u'Order(%s, %s, %s)' % (self.order_number, self.customer, self.grand_total)

    def render_pdf(self):
        return render_template('order_document.html', order=self)

    def _fetch_customer(self, order):
        try:
            links = order.get('links', [])
            customer_links = [link.get('href', '') for link \
                                                  in links \
                                                  if link.get('rel', '') == 'customer']
            if customer_links:
                customer = self.client.get(customer_links[0])
                billing_address = customer.get('billingAddress', {})
                return '%s %s' % (billing_address.get('firstName', ''),
                                  billing_address.get('lastName', ''))
        except epages.RESTError:
            pass
        return u''

class BydOrderViewData(OrderViewData):
    def __init__(self, order, client):
        #super(BydOrderViewData, self).__init__(order, client)
        self.client = client
        self.order_number = order.get('orderNumber', '')
        self.pdf_link = '/api/pdfs/%s.pdf' % order.get('_id', '')
        grand_total = order.get('grandTotal', {})
        self.grand_total = '%s %s' % (grand_total.get('amount', ''),
                                      grand_total.get('currency', ''))
        billing_address = order.get('billingAddress', {})
        self.customer = escape('%s %s' % (billing_address.get('firstName', ''),
                                          billing_address.get('lastName', '')))
        shop = {}
        try:
            shop = self.client.get('/shop')
        except epages.RESTError, error:
            print unicode(error)
        self.shop_name = escape(shop.get('name', ''))
        self.shop_email = shop.get('address', {}).get('email', '')
        self.logo_url = _get_byd_shop_logo(self.client)
        self.billing_name = escape(self.customer)
        self.billing_street = escape('%s %s' % (billing_address.get('street', ''),
                                                billing_address.get('houseNumber', '')))
        self.billing_postcode = escape(billing_address.get('postalCode', ''))
        self.billing_town = escape(billing_address.get('city', ''))

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
        except epages.RESTError, error:
            print unicode(error)
        line_item_container = order.get('lineItemContainer', {})
        product_line_items = line_item_container.get('productLineItems', [])
        self.shipping_total = order.get('shippingData', {}).get('price', {}).get('formatted', None)
        self.products = [ProductViewData(product) for product in product_line_items]

    def _fetch_self_link(self, order):
        links = order.get('links', [])
        self_link = [link.get('href', '') for link in links if link.get('rel', '') == 'self'][0]
        return self_link

class BydOrderExtendedViewData(BydOrderViewData):
    def __init__(self, order, client):
        super(BydOrderExtendedViewData, self).__init__(order, client)
        shipping_lineitem_price = order.get('shippingLineItem', {}).get('lineItemPrice', {})
        self.shipping_total = '%s %s' % (shipping_lineitem_price.get('amount', ''),
                                         shipping_lineitem_price.get('currency', ''))
        self.products = [BydProductViewData(product) for product \
                                                     in order.get('productLineItems', [])]

class ProductViewData(object):
    def __init__(self, product):
        super(ProductViewData, self).__init__()
        self.name = escape(product.get('name', ''))
        self.quantity = product.get('quantity', {}).get('amount', '')
        self.tax = unicode(product.get('taxClass', {}).get('percentage', '')) \
                   .replace('.0', '') + ' %'
        self.price_per_item = product.get('singleItemPrice', {}).get('formatted', '')
        self.price_total = product.get('lineItemPrice', {}).get('formatted', '')
        self.icon = None
        icons = [img for img \
                     in product.get('images', []) \
                     if img.get('classifier', '') == 'Thumbnail']
        if icons:
            self.icon = icons[0].get('url', None)

    def __unicode__(self):
        return u'Product(%s)' % self.name

class BydProductViewData(object):
    def __init__(self, product):
        super(BydProductViewData, self).__init__()
        self.name = escape(product.get('product', {}).get('name', ''))
        self.quantity = product.get('quantity', {}).get('value', '')
        self.tax = unicode(product.get('lineItemTax', {}).get('taxRate', ''))
        unit_price = product.get('unitPrice', {})
        self.price_per_item = u'%s %s' % (unit_price.get('amount', ''),
                                          unit_price.get('currency', ''))
        line_item_price = product.get('lineItemPrice', {})
        self.price_total = u'%s %s' % (line_item_price.get('amount', ''),
                                       line_item_price.get('currency', ''))
        self.icon = product.get('product', {}).get('_links', {}) \
                    .get('default-image-data', {}).get('href', None)
        # Hack to remove the templated parameters breaking valid HTML hyperlinks
        self.icon = re.sub(r'\{.*\}', '', self.icon)
        self.icon += '&width=32'

    def __unicode__(self):
        return u'BydProduct(%s)' % self.name

    def __str__(self):
        return 'BydProduct(%s)' % self.name
