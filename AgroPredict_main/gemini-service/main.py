from flask import Flask, request, jsonify
import vertexai
from vertexai.preview.generative_models import GenerativeModel, ChatSession
import os
from transformers import pipeline
from collections import deque

app = Flask(__name__)

# Initialize Vertex AI
project_id = 'PROJECT_ID'
location = "REGION"
vertexai.init(project=project_id, location=location)

# Initialize the Gemini model
model = GenerativeModel("gemini-1.0-pro")

# Initialize the NLP pipeline for question answering
HF_TOKEN = 'HUGGINGFACE_TOKEN'
nlp = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")

# Context cache
MAX_CONTEXT_LENGTH = 10
context_cache = deque(maxlen=MAX_CONTEXT_LENGTH)

def extract_crop_region_and_time(sentence):
    crop_question = "What crop is mentioned in the sentence?"
    region_question = "Which region is mentioned in the sentence?"
    time_question = "What season or month is mentioned in the sentence?"

    crop_result = nlp(question=crop_question, context=sentence)
    region_result = nlp(question=region_question, context=sentence)
    time_result = nlp(question=time_question, context=sentence)

    crop = crop_result['answer']
    region = region_result['answer']
    time = time_result['answer']

    return crop, region, time

def get_chat_response(prompt: str):
    chat = model.start_chat()
    
    # Add context to the chat session
    for message in context_cache:
        if message.startswith("Human: "):
            chat.send_message(message[7:])  # Remove "Human: " prefix
        elif message.startswith("AI: "):
            # We can't directly add AI responses, so we'll skip them
            pass
    
    response = chat.send_message(prompt)
    context_cache.append(f"Human: {prompt}")
    context_cache.append(f"AI: {response.text}")
    return response.text

@app.route('/analyze', methods=['POST'])
def analyze_crop_suitability():
    request_json = request.get_json(silent=True)
    
    if not request_json or 'sentence' not in request_json:
        return jsonify({"error": "Please provide a sentence in the request"}), 400

    sentence = request_json['sentence']
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
    """

    result = get_chat_response(prompt)
    return jsonify({"crop_analysis": result})

@app.route('/chat', methods=['POST'])
def chat_with_ai():
    request_json = request.get_json(silent=True)
    
    if not request_json or 'message' not in request_json:
        return jsonify({"error": "Please provide a message in the request"}), 400

    message = request_json['message']
    result = get_chat_response(message)
    return jsonify({"response": result})

@app.route('/context', methods=['GET'])
def get_context():
    return jsonify({"context": list(context_cache)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)