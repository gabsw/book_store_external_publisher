import time
import os

import requests
from requests.auth import HTTPBasicAuth

publisher_name = 'External Publisher'
username = 'external_publisher'
password = 'pw'
url = os.getenv('BOOKSTORE_URL', 'localhost:8080')

session = requests.Session()

auth_token = None


def login():
    response = session.get(f'{url}/api/session/login', auth=HTTPBasicAuth(username, password))
    if response.status_code != 200:
        raise Exception('bad credentials')
    return {"x-auth-token": response.headers.get("x-auth-token")}


def get_stock(headers):
    current_page = 0

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
                update_stock(book['isbn'], headers)

        if is_last_page:
            break
        current_page += 1


def update_stock(isbn, headers):
    new_stock = {'isbn': isbn, 'quantity': 10}
    print('Updating book with isbn ', isbn, '.')
    print('Sending 10 new copies to marketplace...')
    response = session.put(f"{url}/api/publisher/{publisher_name}/stock", json=new_stock,
                           headers=headers)

    if response.status_code != 200:
        print("Stock update has failed.")


if __name__ == '__main__':
    while True:
        headers = login()
        get_stock(headers)
        time.sleep(60)
