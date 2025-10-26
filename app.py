import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from azure.storage.blob import BlobServiceClient, ContentSettings, PublicAccess

# Config
STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = "lanternfly-images"

# Initialize Azure
bsc = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
cc = bsc.get_container_client(CONTAINER_NAME)

# Create the container if it doesn’t exist
try:
    cc.create_container(public_access=PublicAccess.Container)
except Exception:
    pass  # Container likely exists

# Flask app
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("gallery.html")

@app.post("/api/v1/upload")
def upload():
    try:
        f = request.files["file"]
        if not f:
            return jsonify(ok=False, error="No file provided"), 400

        if not f.mimetype.startswith("image/"):
            return jsonify(ok=False, error="Only image files allowed"), 400

        # Sanitize + timestamp filename
        safe_name = f.filename.replace(" ", "_")
        blob_name = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}-{safe_name}"

        blob_client = cc.get_blob_client(blob_name)
        blob_client.upload_blob(
            f.read(),
            overwrite=True,
            content_settings=ContentSettings(content_type=f.mimetype)
        )

        url = f"{blob_client.url}"
        return jsonify(ok=True, url=url)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

@app.get("/api/v1/gallery")
def gallery():
    try:
        urls = [f"{cc.url}/{b.name}" for b in cc.list_blobs()]
        return jsonify(ok=True, gallery=urls)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

@app.get("/api/v1/health")
def health():
    return jsonify(ok=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)