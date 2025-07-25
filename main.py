import os
from flask import Flask, jsonify

app = Flask(__name__)

# This new route only accepts GET requests
@app.route('/getsignal', methods=['GET'])
def handle_get_request():
    print("GET request received successfully!")
    # Send back a fixed success message
    return jsonify({"signal": "GET_SUCCESS"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
