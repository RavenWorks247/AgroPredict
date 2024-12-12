### AgroPredict: Deployment and Usage Guide

AgroPredict is an advanced AI-powered crop recommendation system designed to assist farmers in making informed decisions about crop selection based on various environmental and historical factors. This guide will walk you through the steps to deploy and use AgroPredict.

### Prerequisites

- Docker
- Google Cloud SDK
- Python 3.7+

### Step 1: Clone the Repository

Clone the AgroPredict repository to your local machine:

```bash
git clone https://github.com/RavenWorks247/AgroPredict
cd AgroPredict
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

### Step 3: Deploy the Application

Use the `execall.sh` script to deploy all components of AgroPredict:

1. Navigate to the project directory:

   ```bash
   cd AgroPredict
   ```

2. Run the deployment script:

   ```bash
   bash execall.sh
   ```

The `execall.sh` script performs the following actions:

- Deploys the `gemini-service` to Google Cloud Run:

  ```bash
  cd gemini-service
  gcloud builds submit --tag gcr.io/PROJECT_ID/crop-analysis-app
  gcloud run deploy crop-analysis-app \
    --image gcr.io/PROJECT_ID/crop-analysis-app \
    --region ENTER_REGION \
    --memory 16Gi \
    --cpu 4 \
    --platform managed \
    --allow-unauthenticated
  cd ..
  ```

- Builds and pushes the `streamlit-crop-app` Docker image, then deploys it to Google Cloud Run:

  ```bash
  cd streamlit-crop-app
  docker build -t gcr.io/PROJECT_ID/streamlit-crop-app .
  docker push gcr.io/PROJECT_ID/streamlit-crop-app
  gcloud run deploy streamlit-crop-app \
    --image gcr.io/PROJECT_ID/streamlit-crop-app \
    --platform managed \
    --region ENTER_REGION \
    --memory 4Gi \
    --cpu 2 \
    --allow-unauthenticated
  cd ..
  ```

### Project Structure

```
AgroPredict/
├── gemini-service/
│   ├── .env
│   ├── BuildAndDeploy.txt
│   ├── Dockerfile
│   ├── main.py
│   ├── requirements.txt
├── streamlit-crop-app/
│   ├── .streamlit/
│   │   ├── config.toml
│   ├── .env
│   ├── Dockerfile
│   ├── app.py
│   ├── guidefile.txt
│   ├── requirements.txt
├── execall.sh
```

### Technical Details

- **NLP Model**: Utilizes Hugging Face Transformers for NLP tasks.
- **Vertex AI**: Interacts with Vertex AI's Gemini model for detailed analysis.
- **Redis**: Used for caching session contexts to maintain state across requests.
- **Flask**: The web framework used to build the application.
- **Streamlit**: For interactive user interfaces.
- **Google Cloud Run**: The platform for deploying all components as managed containers.

### Conclusion

AgroPredict leverages advanced AI technology to provide precise and actionable insights for farmers. By following this guide, you can deploy AgroPredict on Google Cloud Platform and start making AI-driven decisions in agriculture. Embrace the future of farming with AgroPredict!

For any issues or contributions, feel free to open an issue or a pull request here.

