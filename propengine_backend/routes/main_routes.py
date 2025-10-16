from flask import Blueprint, request, jsonify
from core.input_handler import process_input

main_dp = Blueprint("main", __name__)

@main_dp.route("/analyze", methods = ["POST"])
def analyze_property():
    data = request.get_json()
    result = process_input(data)
    return jsonify(result), 200
