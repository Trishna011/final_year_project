from flask import Flask, request, jsonify
from model.featureEngineering import add_labour_rate, prediction
import pandas as pd
import numpy as np
import joblib

# --- Load model and preprocessing assets ---

app = Flask(__name__)
@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        data = add_labour_rate(data)
        print(data)
        cost = prediction(data)

        response = {
            "predicted_cost": round(cost, 2),
            "currency": "GBP",
            "message": "Prediction successful"
        }
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

