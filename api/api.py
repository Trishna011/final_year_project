import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, request, jsonify
import traceback
from flask_cors import CORS
from model.featureEngineering import add_labour_rate, prediction, expand_records
from modelB.catboost.catBoostFineTuned import predict_cost_from_input
from modelB.preprocessingUserInp import encode, expand_df
import pandas as pd

app = Flask(__name__)
CORS(app)

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()

        # Convert into multiple grouped objects
        expanded_data = expand_records(data)

        print("🔹 Expanded Data:", expanded_data)

        # 👉 Loop for prediction or handle based on your model logic
        results = []
        total_cost = 0
        for d in expanded_data:
            d = add_labour_rate(d)
            cost = prediction(d)
            results.append({**d, "predicted_cost": cost})
            total_cost += float(cost)
        
        return jsonify({
            "result_sets": results,
            "total_predicted_cost": total_cost,
            "currency": "GBP"
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400
    

@app.route("/value", methods=["POST"])
def value():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No input data"}), 400

        # normalize field names
        if "Location" in data:
            data["location"] = data.pop("Location")

        # normalize cost name
        if "cost" in data:
            data["renovation_cost"] = data.pop("cost")

        if "renovation_cost" not in data:
            return jsonify({"error": "Missing renovation_cost"}), 400
        
        # convert request to DataFrame
        df = pd.DataFrame([data])

        # run hybrid value prediction
        df = encode(df)
        expanded_df = expand_df(df)
        post_renovation_value = round(float(predict_cost_from_input(expanded_df)), 2)

        return jsonify({
            "post_renovation_value": post_renovation_value,
            "currency": "GBP"
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400

    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

