from flask import Flask

app = Flask(__name__)

@app.route('/clients/<msisdn>', methods=['GET'])
def client(msisdn):
    if msisdn == "user2":
        return {'msisdn': msisdn,'client_id': 'Иванов', 'contracts': ({'contract': 1, 'status': 'ready'}, {'contract': 2, 'status': 'ready'}, {'contract': 3, 'status': 'ready'} )}
    else:
        return {'msisdn': msisdn,'client_id': 'Петров', 'contracts': ({'contract': 1, 'status': 'noready'}, {'contract': 2, 'status': 'ready'}, {'contract': 3, 'status': 'ready'} )}

if __name__ == '__main__':
    app.run(debug=True, port=8000)