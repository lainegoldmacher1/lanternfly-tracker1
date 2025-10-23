import os
from flask import Flask, request, jsonify, render_template
from azure.storage.blob import BlobServiceClient, ContentSettings
from datetime import datetime
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Load config from environment
STORAGE_ACCOUNT_URL = os.getenv("STORAGE_ACCOUNT_URL")
IMAGES_CONTAINER = os.getenv("IMAGES_CONTAINER")
CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

# Connect to Azure Blob Storage
bsc = BlobServiceClient.from_connection_string(CONNECTION_STRING)
cc = bsc.get_container_client(IMAGES_CONTAINER)

@app.route("/api/v1/upload", methods=["POST"])
def upload():
    try:
        f = request.files.get("file")
        if not f:
            return jsonify(ok=False, error="Missing file"), 400

        if not f.content_type.startswith("image/"):
            return jsonify(ok=False, error="Only image uploads allowed"), 400

        if len(f.read()) > 10 * 1024 * 1024:
            return jsonify(ok=False, error="File too large (max 10MB)"), 400
        f.seek(0)

        filename = secure_filename(f.filename)
        blob_name = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}-{filename}"
        blob_client = cc.get_blob_client(blob_name)
        blob_client.upload_blob(
            f,
            overwrite=True,
            content_settings=ContentSettings(content_type=f.content_type)
        )
        return jsonify(ok=True, url=blob_client.url)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500
@app.route("/api/v1/gallery", methods=["GET"])
def gallery():
    try:
        urls = [f"{STORAGE_ACCOUNT_URL}/{IMAGES_CONTAINER}/{blob.name}" for blob in cc.list_blobs()]
        return jsonify(ok=True, gallery=urls)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True)