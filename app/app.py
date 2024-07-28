from flask import Flask, request, jsonify, send_file, render_template
import os
import threading
import logging
from app.utils import process_csv, handle_file_upload, get_result

# Initialize Flask application
app = Flask(__name__, template_folder='../templates')
# Configure the folder for file uploads
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/', methods=['GET', 'POST'])
def home():
    """Renders the home page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles file upload and starts processing."""
    try:
        # Ensures a file part is present in the request
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400

        # Ensures a file is selected
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Logs the file upload and processes it using 'handle_file_upload
        if file:
            logging.info(f"File uploaded: {file.filename}")
            task_id = handle_file_upload(file, app.config['UPLOAD_FOLDER'])
            logging.info(f"Task ID generated: {task_id}")
            return jsonify({'task_id': task_id}), 202
    except Exception as e:
        logging.error(f"Error during file upload: {e}")
        return jsonify({'error': 'An error occurred during file upload'}), 500

@app.route('/result/<task_id>', methods=['GET'])
def get_file_result(task_id):
    """Retrieves the processed file based on the task ID."""
    try:
        result = get_result(task_id, app.config['UPLOAD_FOLDER'])
        if result:
            return send_file(result)
        else:
            # Check if the file is being processed
            output_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{task_id}_output.csv")
            input_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{task_id}_input.csv")
            if os.path.exists(input_file_path) and not os.path.exists(output_file_path):
                logging.info(f"Task {task_id} is still processing.")
                return jsonify({'status': 'Processing...'}), 202
            logging.info(f"Task {task_id} not found.")
            return jsonify({'status': 'Not found'}), 404
    except Exception as e:
        logging.error(f"Error retrieving result for task {task_id}: {e}")
        return jsonify({'error': f"An error occurred while retrieving the result: {e}"}), 500

if __name__ == '__main__':
    # Run the Flask application in debug mode
    app.run(debug=True)
