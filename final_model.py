import joblib
import argparse
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import content_model 
import headers_model

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Classify an EML file using a trained model.")
parser.add_argument('filename', type=str, help='The name of the .eml file to process')
args = parser.parse_args()

# Process the input file for the content model
print(f"Processing file: {args.filename}")
file_to_test_content = content_model.build_object(args.filename)

if isinstance(file_to_test_content, pd.DataFrame):
    # Extract the 'content' column
    content_column = file_to_test_content['content']

    # Load models and vectorizer
    content_model = joblib.load('content_model.pkl')
    vectorizer = joblib.load('vectorizer.pkl')

    # Preprocess the content
    preprocessed_content = vectorizer.transform(content_column).toarray()

    # Make predictions
    content_prediction = content_model.predict(preprocessed_content)
    print("Content Prediction:", content_prediction)
else:
    print("Error: Failed to process the EML file.")

file_to_test_headers = headers_model.build_object(args.filename)
header_model = joblib.load('headers_model.pkl')
if isinstance(file_to_test_headers, pd.DataFrame):

    # Make predictions
    header_prediction = header_model.predict(file_to_test_headers)
    print("Header Prediction:", header_prediction)


