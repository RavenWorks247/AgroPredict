### AgroPredict: Deployment and Usage Guide

AgroPredict is an advanced AI-powered crop recommendation system designed to assist farmers in making informed decisions about crop selection based on various environmental and historical factors. This guide will walk you through the steps to deploy and use AgroPredict.


### Prerequisites

- Docker
- Google Cloud SDK
- Redis
- Python 3.7+


### Step 1: Clone the Repository

Clone the AgroPredict repository to your local machine:

```bash
git clone https://github.com/RavenWorks247/AgroPredict
cd AgroPredict_main
```


### Step 2: Set Up Google Cloud

1. **Create a Google Cloud Project:**
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project.

2. **Enable APIs:**
   - Enable the Vertex AI API and Cloud Run API for your project.

3. **Set Up Authentication:**
   - Authenticate your Google Cloud SDK:
     ```bash
     gcloud auth login
     ```
   - Set your project ID:
     ```bash
     gcloud config set project YOUR_PROJECT_ID
     ```


### Step 3: Deploy to Google Cloud Run

#### For `gemini-service`:

1. **Submit the Docker Image to Google Container Registry:**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/crop-analysis-app
   ```

2. **Deploy the Container to Cloud Run:**
   ```bash
   gcloud run deploy crop-analysis-app --image gcr.io/PROJECT_ID/crop-analysis-app --platform managed --region REGION --allow-unauthenticated
   ```


### Step 4: Build the Cloud Functions

1. **Navigate to the `crop-analysis-function` directory:**
   ```bash
   cd ../crop-analysis-function
   ```

2. **Deploy the cloud function named analyze_crop_suitability:**
   ```bash
   gcloud functions deploy analyze_crop_suitability --runtime python39 --trigger-http --allow-unauthenticated --project PROJECT_ID
   ```

3. **Deploy the cloud function named get_context:**
   ```bash
   gcloud functions deploy get_context --runtime python39 --trigger-http --allow-unauthenticated --project PROJECT_ID
   ```

### Step 6: Using AgroPredict

   -**Navigate to the `AgroPredict_main` directory:**
    ```bash
    cd ..
    ```

#### Analyzing Crop Suitability

1. **Endpoint:**
   - The `/analyze` endpoint in the `crop-analysis-function` service is used to analyze the suitability of growing a specific crop in a specific region in a specific time or season.

2. **Request:**
   - Send a POST request to the `/analyze` endpoint with a JSON payload containing the sentence for the Main prompt.
   - Example:
     ```bash
     curl -m 70 -X POST https://REGION-PROJECT_ID.cloudfunctions.net/analyze_crop_suitability \
     -H "Authorization: bearer $(gcloud auth print-identity-token)" \
     -H "Content-Type: application/json" \
     -d '{
       "sentence": "Can I grow wheat in Rajasthan during summer?"
     }' > output.json
     python stranalysis.py
     ```

3. **Response:**
   - The response will contain the analysis of crop suitability.

2. **Request:**
   - Send a POST request to the `/chat` endpoint with a JSON payload containing the sentence for the Chat prompt.
   - Example:
     ```bash
     curl -m 70 -X POST https://REGION-PROJECT_ID.cloudfunctions.net/analyze_crop_suitability \
     -H "Authorization: bearer $(gcloud auth print-identity-token)" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Tell me more about crops that can be grown in Rajasthan."
     }' > output.json
     python strresponse.py
     ```

3. **Response:**
   - The response will contain the response to the message you sent in relation with the context.


### Project Structure

```
AgroPredict_main/
├── crop-analysis-function/
│   ├── DeployComm.txt
│   ├── main.py
│   ├── requirements.txt
├── gemini-service/
│   ├── BuildAndDeploy.txt
│   ├── Dockerfile
│   ├── main.py
│   ├── requirements.txt
├── Execution codes.txt
├── stranalysis.py
├── strresponse.py
```


### Technical Details

- **NLP Model**: Utilizes Hugging Face Transformers for NLP tasks.
- **Vertex AI**: Interacts with Vertex AI's Gemini model for detailed analysis.
- **Redis**: Used for caching session contexts to maintain state across requests.
- **Flask**: The web framework used to build the application.
- **Gunicorn**: The WSGI server used to run the Flask application in production.


### Conclusion

AgroPredict leverages advanced AI technology to provide precise and actionable insights for farmers. By following this guide, you can deploy AgroPredict on Google Cloud Platform and start making AI-driven decisions in agriculture. Embrace the future of farming with AgroPredict!

For any issues or contributions, feel free to open an issue or a pull request here.
