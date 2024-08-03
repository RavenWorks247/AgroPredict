import functions_framework
import requests
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Cloud Run service URL
GEMINI_SERVICE_URL = 'CLOUD_RUN_SERVICE_URL'

@functions_framework.http
def analyze_crop_suitability(request):
    try:
        logging.info(f"GEMINI_SERVICE_URL: {GEMINI_SERVICE_URL}")
        
        if request.method == 'OPTIONS':
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '3600'
            }
            return ('', 204, headers)

        headers = {
            'Access-Control-Allow-Origin': '*'
        }

        request_json = request.get_json(silent=True)
        
        if not request_json:
            logging.error(f"Invalid request: {request_json}")
            return ({"error": "Please provide a valid JSON request"}, 400, headers)

        # Determine which endpoint to call based on the request
        if 'sentence' in request_json:
            endpoint = '/analyze'
        elif 'message' in request_json:
            endpoint = '/chat'
        else:
            logging.error(f"Invalid request format: {request_json}")
            return ({"error": "Please provide either 'sentence' for crop analysis or 'message' for chat"}, 400, headers)

        logging.info(f"Sending request to Gemini service: {request_json}")
        full_url = f"{GEMINI_SERVICE_URL}{endpoint}"
        logging.info(f"Full URL: {full_url}")
        response = requests.post(full_url, json=request_json, timeout=30)
        
        logging.info(f"Response status code: {response.status_code}")
        logging.info(f"Response content: {response.text}")

        if response.status_code != 200:
            logging.error(f"Gemini service returned non-200 status code: {response.status_code}")
            logging.error(f"Gemini service response: {response.text}")
            return ({"error": "Error from Gemini service"}, 500, headers)

        logging.info("Successfully received response from Gemini service")
        return (response.json(), response.status_code, headers)

    except requests.RequestException as e:
        logging.error(f"Request to Gemini service failed: {str(e)}")
        return ({"error": "Failed to communicate with Gemini service"}, 500, headers)

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return ({"error": "An unexpected error occurred"}, 500, headers)

@functions_framework.http
def get_context(request):
    try:
        if request.method == 'OPTIONS':
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '3600'
            }
            return ('', 204, headers)

        headers = {
            'Access-Control-Allow-Origin': '*'
        }

        full_url = f"{GEMINI_SERVICE_URL}/context"
        response = requests.get(full_url, timeout=30)

        if response.status_code != 200:
            logging.error(f"Gemini service returned non-200 status code: {response.status_code}")
            logging.error(f"Gemini service response: {response.text}")
            return ({"error": "Error retrieving context from Gemini service"}, 500, headers)

        logging.info("Successfully retrieved context from Gemini service")
        return (response.json(), response.status_code, headers)

    except requests.RequestException as e:
        logging.error(f"Request to Gemini service failed: {str(e)}")
        return ({"error": "Failed to communicate with Gemini service"}, 500, headers)

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return ({"error": "An unexpected error occurred"}, 500, headers)