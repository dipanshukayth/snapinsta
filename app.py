import os
import time
import uuid
import base64
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory storage (Zero se test karne ke liye)
# Har item: {"id": str, "image_url": str, "type": "post"|"snap", "caption": str, "created_at": float}
POSTS = []

# Snaps ko 60 seconds me expire karne ka timer (testing ke liye)
SNAP_EXPIRY_SECONDS = 60


def clean_expired_snaps():
    """Purane snaps ko memory aur disk se hatao"""
    current_time = time.time()
    active_posts = []
    for item in POSTS:
        if item["type"] == "snap" and (current_time - item["created_at"]) > SNAP_EXPIRY_SECONDS:
            filepath = os.path.join(".", item["image_url"].lstrip("/"))
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass
        else:
            active_posts.append(item)
    POSTS.clear()
    POSTS.extend(active_posts)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/feed", methods=["GET"])
def get_feed():
    clean_expired_snaps()
    # Naye posts sabse upar
    return jsonify(sorted(POSTS, key=lambda x: x["created_at"], reverse=True))


@app.route("/api/upload", methods=["POST"])
def upload_media():
    clean_expired_snaps()
    data = request.get_json()

    image_data = data.get("image")  # base64 string
    post_type = data.get("type", "post")  # 'snap' ya 'post'
    caption = data.get("caption", "").strip()

    if not image_data:
        return jsonify({"error": "No image data"}), 400

    # Base64 string ko image file me save karna
    header, encoded = image_data.split(",", 1)
    file_bytes = base64.b64decode(encoded)
    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    with open(filepath, "wb") as f:
        f.write(file_bytes)

    new_item = {
        "id": uuid.uuid4().hex,
        "image_url": f"/static/uploads/{filename}",
        "type": post_type,
        "caption": caption,
        "created_at": time.time(),
    }
    POSTS.append(new_item)

    return jsonify({"success": True, "item": new_item})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
