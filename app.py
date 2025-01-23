import os
import base64
import google.generativeai as gem
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import pandas as pd
import ast
import json
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Global API key
GOOGLE_API_KEY = 'AIzaSyDc8qqXA7dKKExF5sm_dFISijUU5vHatls'  # Replace with your actual API key

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def image_to_base64(image_path):
    """Convert image to base64 encoding"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def process_single_image(image_path, llm, vision):
    """Process a single business card image"""
    image_base64 = image_to_base64(image_path)

    # Business card validation
    res = vision.generate_content([
        "You are only a business card image recognizer, you will tell clean 'YES' if it is it else clean 'NO'",
        {"mime_type": "image/jpeg", "data": image_base64}
    ])

    if res.text == 'NO':
        return None

    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": """Carefully analyze the business card and extract data in this precise JSON format:
                {
                    "person_name": "Full Name",
                    "company_name": "Company Name",
                    "email": "Email Address",
                    "contact_number": "Phone Number"
                }
                Ensure all fields are extracted accurately.""",
            },
            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_base64}"}
        ]
    )

    try:
        response = llm.invoke([message])
        # Clean and parse the response
        response_text = response.content.replace('```json', '').replace('```', '').strip()
        extracted_data = json.loads(response_text)
        return extracted_data
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return None


def process_all_images(image_files):
    """Process multiple business card images"""
    # Configure Google AI
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    gem.configure(api_key=GOOGLE_API_KEY)

    # Initialize models
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest")
    vision = gem.GenerativeModel('gemini-1.5-flash-latest')

    # Extract data from all images
    all_extracted_data = []
    for image_file in image_files:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file)
        extracted_data = process_single_image(image_path, llm, vision)
        if extracted_data:
            all_extracted_data.append(extracted_data)

    return all_extracted_data


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({'error': 'No files uploaded'})

    files = request.files.getlist('files')
    uploaded_files = []

    for file in files:
        if file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            uploaded_files.append(filename)

    if not uploaded_files:
        return jsonify({'error': 'No valid files uploaded'})

    try:
        # Process all uploaded images
        extracted_data = process_all_images(uploaded_files)
        return jsonify({'data': extracted_data})
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/download', methods=['POST'])
def download_csv():
    data = request.json.get('data', [])
    df = pd.DataFrame(data)
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], 'business_cards.csv')
    df.to_csv(csv_path, index=False)
    return send_file(csv_path, as_attachment=True)


@app.route('/clear', methods=['POST'])
def clear_uploads():
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")
    return jsonify({'status': 'success'})


if __name__ == '__main__':
    app.run(debug=True)