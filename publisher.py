import os

import requests
from requests.auth import HTTPBasicAuth
from flask import Flask, jsonify

publisher_name = 'External Publisher'
username = 'external_publisher'
password = 'pw'
url = os.getenv('BOOKSTORE_URL', 'localhost:8080')

session = requests.Session()

auth_token = None

app = Flask(__name__)


@app.route('/api/external-publisher/stock/automatic-renewal', methods=['GET'])
def stock_renewal():
    headers = login()
    stock = renew_stock(headers)
    return jsonify(stock)


@app.route('/api/external-publisher/stock/sold-out', methods=['GET'])
def get_sold_out_books():
    headers = login()
    books = fetch_sold_out_books(headers)
    return jsonify(books)


def login():
    response = session.get(f'{url}/api/session/login', auth=HTTPBasicAuth(username, password))
    if response.status_code != 200:
        raise Exception('bad credentials')
    return {"x-auth-token": response.headers.get("x-auth-token")}


def fetch_sold_out_books(headers):
    current_page = 0
    sold_out_books = []

    while True:
        response = session.get(f"{url}/api/publisher/{publisher_name}/stock?page={current_page}",
                               headers=headers)
        book_page = response.json()
        is_last_page = book_page['last']

        books = book_page['content']
        for book in books:
            if book['quantity'] == 0:
                sold_out_books.append(book)

        if is_last_page:
            break
        current_page += 1

    return sold_out_books


def renew_stock(headers):
    current_page = 0
    renewed_stock = []

    print('Retrieving stock from book store...')

    while True:
        response = session.get(f"{url}/api/publisher/{publisher_name}/stock?page={current_page}",
                               headers=headers)
        book_page = response.json()
        is_last_page = book_page['last']

        books = book_page['content']
        for book in books:
            print('Checking book for stock: ', book)
            if book['quantity'] == 0:
                print(book['title'], ' has 0 copies in stock.')
                renewed_stock = update_book(book['isbn'], headers)

        if is_last_page:
            break
        current_page += 1

    return renewed_stock


def update_book(isbn, headers):
    new_stock = {'isbn': isbn, 'quantity': compute_quantity(headers)}
    print('Updating book with isbn ', isbn, '.')
    print('Sending 10 new copies to marketplace...')
    response = session.put(f"{url}/api/publisher/{publisher_name}/stock", json=new_stock,
                           headers=headers)

    if response.status_code != 200:
        print("Stock update has failed.")
        return {'isbn': isbn, 'quantity': 0}
    else:
        return new_stock


def compute_quantity(headers):
    response = session.get(f"{url}/api/publisher/{publisher_name}/revenue/total",
                           headers=headers)

    if response.status_code != 200:
        print("Revenue check has failed.")
        return 0

    amount = response.json()

    if amount < 100:
        return 5
    elif amount < 500:
        return 10
    elif amount < 1000:
        return 20
    else:
        return 50


if __name__ == '__main__':
    app.run(host='0.0.0.0')
