from flask import Flask, request, jsonify
from services.payment_processor import PaymentProcessorService

app = Flask(__name__)


@app.route("/api/v2/payments/process", methods=["POST"])
def process_payment():
    data = request.get_json()

    required_fields = ["user_id", "user_email", "amount", "resource_id", "payment_provider"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    try:
        result = PaymentProcessorService.process_payment(
            user_id=data["user_id"],
            user_email=data["user_email"],
            amount=float(data["amount"]),
            resource_id=data["resource_id"],
            payment_provider=data["payment_provider"],
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500

    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 402


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
