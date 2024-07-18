from datetime import datetime

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from S3_bucket import get_file_from_s3, upload_file_to_s3, download_last_modified_file_from_s3
from llm_model import generate_content_from_documents, generate_content
from create_database import generate_data_store
from weatherAPI import get_weather_alerts
from auth import authenticate

app = Flask(__name__)
CORS(app)

host = "https://devhack-genai.onrender.com"


@app.route('/')
def index():
    return render_template('index.html', host=host)


@app.route('/api/analyze_risk_profile', methods=['POST'])
def analyze_risk_profile():
    if 'Authorization' in request.headers:
        auth_token = request.headers['Authorization']
        is_authenticated = authenticate(auth_token)
        if not is_authenticated:
            return jsonify({'message': 'Please Give Correct API Key'}), 401
        body = request.get_json()
        category = body.get('category')
        industry = body.get('industry') or "any"
        zip_code = body.get('zip')
        state = body.get('state')
        age = body.get('age') or "any"
        # policy_number = body.get('policyNumber')
        claims_data = body.get('claimsdata')
        if not category or not industry or not zip_code or not state or not age:
            return jsonify({'message': 'Please Give All Required Fields'}), 400
        if category in ["safety", "regulations", "vicinity"]:
            if category == "vicinity":
                weather_data = get_weather_alerts()
                if weather_data is None:
                    return jsonify({
                        'response': 'No vicinity Data for today.',
                        "date": datetime.now().date().strftime("%Y-%m-%d"),
                    }), 200
                response = generate_content(weather_data)
                # upload_file_to_s3(data=response, category=category, industry=industry, state=state)
                return jsonify({'response': response, "date": datetime.now().date().strftime("%Y-%m-%d")}), 200
            else:
                prefix = f"archive/{category}/"
                response = download_last_modified_file_from_s3(prefix=prefix, industry=industry,
                                                               state=state)
                if response is not None:
                    return response, 200
                else:
                    return jsonify({'message': f'NO {category} for today.'}), 400
        else:
            return jsonify({'message': 'Please Give Correct Category'}), 400
    else:
        return jsonify({'message': 'Please Give API Key'}), 401


@app.route('/api/get_genai_data', methods=['POST'])
def get_genai_data():
    if 'Authorization' in request.headers:
        auth_token = request.headers['Authorization']
        is_authenticated = authenticate(auth_token)
        if not is_authenticated:
            return jsonify({'message': 'Please Give Correct API Key'}), 401
        # get body data
        category = request.get_json().get('category')
        if category not in ["safety", "regulations", "vicinity"]:
            return jsonify({'message': 'Please Give Correct Category'}), 400
        if category == "safety":
            response = get_file_from_s3("safety/")
            return jsonify({'data': response}), 200
        elif category == "regulations":
            response = get_file_from_s3("regulations/")
            return jsonify({'data': response}), 200
        elif category == "vicinity":
            response = get_file_from_s3("vicinity/")
            return jsonify({'data': response}), 200
        else:
            return jsonify({'message': 'Please Give Correct Category'}), 400
    else:
        return jsonify({'message': 'Please Give an API Key'}), 401


@app.route('/api/generate_risk_profile', methods=['POST'])
def generate_risk_profile():
    if 'Authorization' in request.headers:
        auth_token = request.headers['Authorization']
        is_authenticated = authenticate(auth_token)
        if not is_authenticated:
            return jsonify({'message': 'Please Give Correct API Key'}), 401
        body = request.get_json()
        category = body.get('category')
        industry = body.get('industry') or "any"
        zip_code = body.get('zip')
        state = body.get('state')
        age = body.get('age') or "any"
        # policy_number = body.get('policyNumber')
        claims_data = body.get('claimsdata')
        if not category or not industry or not zip_code or not state or not age or not claims_data:
            return jsonify({'message': 'Please Give All Required Fields'}), 400
        if category in ["safety", "regulations", "vicinity"]:
            if category == "vicinity":
                weather_data = get_weather_alerts()
                if weather_data is None:
                    return jsonify({'message': 'Unable to fetch the Vicinity data.'}), 400
                response = generate_content(weather_data)
                upload_file_to_s3(data=response, category=category, industry=industry, state=state)
                return jsonify({'response': response, "date": datetime.now().date().strftime("%Y-%m-%d")}), 200
            else:
                response = generate_content_from_documents(category=category, industry=industry, state=state, age=age,
                                                           zip_code=zip_code, claims_data=claims_data)
                if response is not None:
                    return response, 200
                else:
                    return jsonify({'message': f'NO {category} for today.'}), 400
        else:
            return jsonify({'message': 'Please Give Correct Category'}), 400
    else:
        return jsonify({'message': 'Please Give API Key'}), 401


@app.route('/api/load_files_to_chunks', methods=['POST'])
def load_files_to_chunks():
    if 'Authorization' in request.headers:
        auth_token = request.headers['Authorization']
        is_authenticated = authenticate(auth_token)
        if not is_authenticated:
            return jsonify({'message': 'Please Give Correct API Key'}), 401
        category = request.get_json().get('category')
        response = generate_data_store(f"{category}/")
        return jsonify({'data': response}), 200
    else:
        return jsonify({'message': 'Please Give API Key'}), 401


if __name__ == '__main__':
    app.run(debug=True)
