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
cd streamlit-crop-app
docker build -t gcr.io/PROJECT_ID/streamlit-crop-app .
docker push gcr.io/PROJECT_ID/streamlit-crop-app
gcloud run deploy streamlit-crop-app --image gcr.io/PROJECT_ID/streamlit-crop-app --platform managed --region ENTER_REGION --memory 4Gi --cpu 2 --allow-unauthenticated
cd ..