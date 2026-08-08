#!/usr/bin/env python3

from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "service": "cloudshift-app"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
