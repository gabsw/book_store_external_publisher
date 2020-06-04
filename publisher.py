import os

import requests
from requests.auth import HTTPBasicAuth
from flask import Flask, jsonify, render_template

publisher_name = 'External Publisher'
username = 'external_publisher'
password = 'pw'
url = os.getenv('BOOKSTORE_URL', 'http://localhost:8080')
port = int(os.getenv('PORT', 5000))

session = requests.Session()

auth_token = None

app = Flask(__name__)


@app.route('/api/stock/renew', methods=['GET'])
def stock_renewal():
    headers = login()
    stock = renew_stock(headers)
    return jsonify(stock)


@app.route('/api/stock/sold-out', methods=['GET'])
def get_sold_out_books():
    headers = login()
    books = fetch_sold_out_books(headers)
    return jsonify(books)


@app.route('/', methods=['GET'])
def get_api_doc():
    return render_template('api-doc.html', title='External Publisher API')


def login():
    response = session.get(f'{url}/api/session/login', auth=HTTPBasicAuth(username, password))
    if response.status_code != 200:
        raise Exception('bad credentials')
    return {"x-auth-token": response.headers.get("x-auth-token")}


def fetch_sold_out_books(headers):
    current_page = 0
    sold_out_books = []

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
                sold_out_books.append(book)

        if is_last_page:
            break
        current_page += 1

    return sold_out_books


def renew_stock(headers):
    sold_out_books = fetch_sold_out_books(headers)
    renewed_stock = [update_book(book['isbn'], headers) for book in sold_out_books]
    return renewed_stock


def update_book(isbn, headers):
    new_stock = {'isbn': isbn, 'quantity': compute_quantity(headers)}
    if new_stock['quantity'] is None:
        return {'isbn': isbn, 'error': 'Revenue check has failed.'}

    print('Updating book with isbn ', isbn, '.')
    print('Sending 10 new copies to marketplace...')
    response = session.put(f"{url}/api/publisher/{publisher_name}/stock", json=new_stock,
                           headers=headers)

    if response.status_code != 200:
        print("Stock update has failed.")
        return {'isbn': isbn, 'error': 'Stock update has failed.'}
    else:
        return new_stock


def compute_quantity(headers):
    response = session.get(f"{url}/api/publisher/{publisher_name}/revenue/total",
                           headers=headers)

    if response.status_code != 200:
        print("Revenue check has failed.")
        return None

    amount = response.json()

    if amount < 150:
        return 5
    elif amount < 500:
        return 10
    elif amount < 1000:
        return 20
    else:
        return 50


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
