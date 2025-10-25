from flask import Blueprint, jsonify, request

# 👇 Define blueprint (no need to repeat /testing in routes)
testing_bp = Blueprint('testing_bp', __name__)

# Route: /testing/
@testing_bp.route('/', methods=['GET'])
def testing_home():
    return jsonify({"message": "Testing route working perfectly!"})

# Route: /testing/data
@testing_bp.route('/data', methods=['POST'])
def testing_data():
    data = request.get_json()
    return jsonify({
        "received_data": data,
        "status": "success"
    })
