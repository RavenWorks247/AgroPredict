cd gemini-service
gcloud builds submit --tag gcr.io/tryinhard/crop-analysis-app
gcloud run deploy crop-analysis-app \
  --image gcr.io/tryinhard/crop-analysis-app \
  --region us-east1 \
  --memory 16Gi \
  --cpu 4 \
  --platform managed \
  --allow-unauthenticated
cd ..
cd streamlit-crop-app
docker build -t gcr.io/tryinhard/streamlit-crop-app .
docker push gcr.io/tryinhard/streamlit-crop-app
gcloud run deploy streamlit-crop-app --image gcr.io/tryinhard/streamlit-crop-app --platform managed --region us-east1 --memory 4Gi --cpu 2 --allow-unauthenticated
cd ..