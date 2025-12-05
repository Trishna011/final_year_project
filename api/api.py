import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, request, jsonify
import traceback
from flask_cors import CORS
from model.featureEngineering import add_labour_rate, prediction, expand_records

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


    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

