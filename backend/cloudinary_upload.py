import os

import cloudinary
import cloudinary.uploader


# =========================================================
# CONFIG CLOUDINARY
# =========================================================

cloudinary.config(
    cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
    api_key=os.environ["CLOUDINARY_API_KEY"],
    api_secret=os.environ["CLOUDINARY_API_SECRET"],
    secure=True,
)


# =========================================================
# UPLOAD IMAGE
# =========================================================

def upload_image(image):
    result = cloudinary.uploader.upload(
        image,
        folder="final_app/users",
        resource_type="image",
    )

    return {
        "public_id": result["public_id"],
        "image_url": result["secure_url"],
    }