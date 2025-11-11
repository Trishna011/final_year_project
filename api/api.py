from flask import Flask, request, jsonify
import traceback
from flask_cors import CORS
from model.featureEngineering import add_labour_rate, prediction

app = Flask(__name__)
CORS(app)

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        data = add_labour_rate(data)
        cost = prediction(data)
        return jsonify({
            "predicted_cost": round(cost, 2),
            "currency": "GBP",
            "message": "Prediction successful"
        }), 200

    except Exception as e:
        print("❌ Full traceback:")
        traceback.print_exc()
        print("❌ Error message:", str(e))
        return jsonify({"error": str(e)}), 400

    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

