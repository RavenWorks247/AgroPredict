import flask
from flask import request, jsonify
import vertexai
from vertexai.preview.generative_models import GenerativeModel, ChatSession
import os
from transformers import pipeline
from collections import deque
from typing import List, Tuple, Dict
import time as time_module
from google.cloud import storage
import json
from dotenv import load_dotenv
load_dotenv()

app = flask.Flask(__name__)

project_id = os.getenv('PROJECT_ID')
location = os.getenv('LOCATION')
vertexai.init(project=project_id, location=location)

model = GenerativeModel("gemini-1.5-flash-002")

HF_TOKEN = os.getenv('HF_TOKEN')
nlp = pipeline("question-answering", model="deepset/roberta-base-squad2")

MAX_CONTEXT_LENGTH = 10
CONTEXT_EXPIRY_TIME = 3600  # 1 hour in seconds
context_cache = {}  # In-memory context for active sessions

BUCKET_NAME = 'CLOUD_STORAGE_BUCKET_NAME'  # Your Google Cloud Storage bucket name
storage_client = storage.Client()

def load_context_from_bucket(user_id: str, session_id: str):
    """Load context from Google Cloud Storage for a given user_id and session_id."""
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f'users/{user_id}/contexts/{session_id}.json')
    
    if blob.exists():
        data = blob.download_as_text()
        context_cache[f"{user_id}_{session_id}"] = deque(json.loads(data), maxlen=MAX_CONTEXT_LENGTH)
    else:
        context_cache[f"{user_id}_{session_id}"] = deque(maxlen=MAX_CONTEXT_LENGTH)

def save_context_to_bucket(user_id: str, session_id: str):
    """Save context to Google Cloud Storage for a given user_id and session_id."""
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f'users/{user_id}/contexts/{session_id}.json')
    
    # Serialize the context to a JSON-compatible format
    data = json.dumps([{'role': item['role'], 'content': item['content'], 'timestamp': item['timestamp']} for item in context_cache[f"{user_id}_{session_id}"]])
    blob.upload_from_string(data)

def clear_context_in_bucket(user_id: str, session_id: str):
    """Clear context in Google Cloud Storage for a given user_id and session_id."""
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f'users/{user_id}/contexts/{session_id}.json')
    
    if blob.exists():
        blob.delete()

def extract_crop_region_and_time(sentence: str) -> Tuple[str, str, str]:
    # Crop, region, and time extraction logic remains the same
    crop_question = "What crop is mentioned in the sentence? Just return the crop name, not a sentence, return nothing if answer cannot be found"
    region_question = "Which region is mentioned in the sentence? Just return the region name, not a sentence, return nothing if answer cannot be found"
    time_question = "What season or month is mentioned in the sentence? Just return the season or month name, not a sentence, nothing"

    crop_result = nlp(question=crop_question, context=sentence)
    region_result = nlp(question=region_question, context=sentence)
    time_result = nlp(question=time_question, context=sentence)

    crop = crop_result['answer']
    region = region_result['answer']
    time = time_result['answer']

    return crop, region, time

def clean_context(user_id: str, session_id: str):
    """Ensure the context is fresh and remove expired items."""
    cache_key = f"{user_id}_{session_id}"
    if cache_key not in context_cache:
        load_context_from_bucket(user_id, session_id)
    
    current_time = time_module.time()
    while context_cache[cache_key] and current_time - context_cache[cache_key][0]['timestamp'] > CONTEXT_EXPIRY_TIME:
        context_cache[cache_key].popleft()

def get_chat_response(user_id: str, session_id: str, prompt: str) -> str:
    """Generate a chat response using the AI model."""
    clean_context(user_id, session_id)
    cache_key = f"{user_id}_{session_id}"
    chat = model.start_chat()
    
    # Add all previous human messages to the context
    for message in context_cache[cache_key]:
        if message['role'] == 'human':
            chat.send_message(message['content'])
    
    response = chat.send_message(prompt)
    
    # Update the in-memory context and save it to GCS
    context_cache[cache_key].append({'role': 'human', 'content': prompt, 'timestamp': time_module.time()})
    context_cache[cache_key].append({'role': 'ai', 'content': response.text, 'timestamp': time_module.time()})
    save_context_to_bucket(user_id, session_id)  # Save updated context
    
    return response.text

@app.route('/analyze', methods=['POST'])
def analyze_crop_suitability():
    request_json = request.get_json(silent=True)
    
    if not request_json or 'sentence' not in request_json or 'session_id' not in request_json or 'user_id' not in request_json:
        return jsonify({"error": "Please provide a sentence, session_id, and user_id in the request"}), 400

    sentence = request_json['sentence']
    session_id = request_json['session_id']
    user_id = request_json['user_id']
    crop, region, time = extract_crop_region_and_time(sentence)
    
    if not crop or not region:
        return jsonify({"error": "Could not extract crop and region from the sentence"}), 400

    prompt = f"""
    Analyze the suitability of growing {crop} in {region} during {time}. Consider the following factors:
    1. Climatic conditions of {region} during {time} in the near future
    2. Soil conditions of {region}
    3. {crop}'s requirements for successful growth, particularly during {time}
    4. Best time period for growing {crop} in {region}, and how {time} aligns with this
    5. Any potential challenges or considerations specific to {time}

    Provide a detailed analysis and recommend whether {crop} is suitable for {region} during {time}. 
    If not entirely suitable, suggest alternative crops that would be more appropriate for the region and time period.
    Also, provide any adjustments in farming practices that might be necessary for {time}.

    Make sure to explicitly mention the typical weather conditions expected in {region} during {time} in your response.
    Ignore and don't mention if there's any repeated nonsensical phrase present.
    """

    result = get_chat_response(user_id, session_id, prompt)
    return jsonify({"crop_analysis": result})

@app.route('/chat', methods=['POST'])
def chat_with_ai():
    request_json = request.get_json(silent=True)
    
    if not request_json or 'message' not in request_json or 'session_id' not in request_json or 'user_id' not in request_json:
        return jsonify({"error": "Please provide a message, session_id, and user_id in the request"}), 400

    message = request_json['message']
    session_id = request_json['session_id']
    user_id = request_json['user_id']
    result = get_chat_response(user_id, session_id, message)
    return jsonify({"response": result})

@app.route('/context', methods=['GET'])
def get_context():
    user_id = request.args.get('user_id')
    session_id = request.args.get('session_id')
    if not user_id or not session_id:
        return jsonify({"error": "Please provide user_id and session_id"}), 400
    
    cache_key = f"{user_id}_{session_id}"
    if cache_key not in context_cache:
        load_context_from_bucket(user_id, session_id)
    
    clean_context(user_id, session_id)
    return jsonify({"context": [{'role': item['role'], 'content': item['content']} for item in context_cache[cache_key]]})

@app.route('/clear_context', methods=['POST'])
def clear_context():
    request_json = request.get_json(silent=True)
    if not request_json or 'session_id' not in request_json or 'user_id' not in request_json:
        return jsonify({"error": "Please provide a session_id and user_id in the request"}), 400

    session_id = request_json['session_id']
    user_id = request_json['user_id']
    cache_key = f"{user_id}_{session_id}"
    context_cache[cache_key] = deque(maxlen=MAX_CONTEXT_LENGTH)
    clear_context_in_bucket(user_id, session_id)
    return jsonify({"message": f"Context cleared for user {user_id}, session {session_id}"})

@app.route('/save_session', methods=['POST'])
def save_session():
    request_json = request.get_json(silent=True)
    if not request_json or 'user_id' not in request_json or 'session_id' not in request_json or 'session_data' not in request_json:
        return jsonify({"error": "Please provide user_id, session_id, and session_data in the request"}), 400

    user_id = request_json['user_id']
    session_id = request_json['session_id']
    session_data = request_json['session_data']

    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"users/{user_id}/sessions/{session_id}/data.json")
    blob.upload_from_string(json.dumps(session_data), content_type='application/json')

    return jsonify({"message": f"Session saved for user {user_id}, session {session_id}"})

@app.route('/load_session', methods=['GET'])
def load_session():
    user_id = request.args.get('user_id')
    session_id = request.args.get('session_id')
    if not user_id or not session_id:
        return jsonify({"error": "Please provide user_id and session_id"}), 400

    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"users/{user_id}/sessions/{session_id}/data.json")
    
    if blob.exists():
        session_data = json.loads(blob.download_as_text())
        return jsonify(session_data)
    else:
        return jsonify({"error": "Session not found"}), 404

@app.route('/list_sessions', methods=['GET'])
def list_sessions():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "Please provide user_id"}), 400

    bucket = storage_client.bucket(BUCKET_NAME)
    blobs = bucket.list_blobs(prefix=f"users/{user_id}/sessions/")
    sessions = {}
    for blob in blobs:
        if blob.name.endswith('/data.json'):
            session_id = blob.name.split('/')[-2]
            sessions[session_id] = blob.time_created.isoformat()
    return jsonify(sessions)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)