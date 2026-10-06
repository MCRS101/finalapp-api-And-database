from flask import Flask, request, jsonify
from flask_cors import CORS
from database import get_connection, init_database

from cloudinary_upload import upload_image
# =========================================================
# FLASK
# =========================================================

app = Flask(__name__)
CORS(app)

# =========================================================
# INITIALIZE DATABASE
# =========================================================

try:
    init_database()
except Exception as e:
    print("====================================")
    print("DATABASE ERROR")
    print(e)
    print("====================================")


# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "success": True,
        "message": "Household API is running"
    })


# =========================================================
# REGISTER
# =========================================================

@app.route("/api/register", methods=["POST"])
def register():

    name = request.form.get("name")
    username = request.form.get("username")
    password = request.form.get("password")
    image = request.files.get("image")

    print("====================================")
    print("REGISTER")
    print("Name:", name)
    print("Username:", username)
    print("Image:", image.filename if image else None)
    print("====================================")

    # =====================================================
    # CHECK DATA
    # =====================================================

    if not name or not username or not password:
        return jsonify({
            "success": False,
            "message": "กรุณากรอกข้อมูลให้ครบ"
        }), 400

    if image is None:
        return jsonify({
            "success": False,
            "message": "กรุณาเลือกรูปภาพ"
        }), 400

    # =====================================================
    # DATABASE
    # =====================================================

    connection = get_connection()

    if connection is None:
        return jsonify({
            "success": False,
            "message": "ไม่สามารถเชื่อมต่อ Database ได้"
        }), 500

    cursor = None

    try:

        cursor = connection.cursor(dictionary=True)

        # =================================================
        # CHECK USERNAME
        # =================================================

        cursor.execute(
            "SELECT id FROM users WHERE username = %s",
            (username,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({
                "success": False,
                "message": "Username นี้มีอยู่แล้ว"
            }), 409

        # =================================================
        # UPLOAD TO CLOUDINARY
        # =================================================

        print("Uploading image to Cloudinary...")

        cloudinary_result = upload_image(image)

        image_url = cloudinary_result["image_url"]
        public_id = cloudinary_result["public_id"]

        print("Cloudinary upload success")
        print("Public ID:", public_id)
        print("Image URL:", image_url)

        # =================================================
        # INSERT DATABASE
        # =================================================

        cursor.execute("""
            INSERT INTO users (
                name,
                username,
                password,
                image_path
            )
            VALUES (%s, %s, %s, %s)
        """, (
            name,
            username,
            password,
            image_url
        ))

        connection.commit()

        user_id = cursor.lastrowid

        print("REGISTER SUCCESS:", user_id)

        return jsonify({
            "success": True,
            "message": "สมัครสมาชิกสำเร็จ",
            "user": {
                "id": user_id,
                "name": name,
                "username": username,
                "image_path": image_url
            }
        }), 201

    except Exception as e:

        connection.rollback()

        print("REGISTER ERROR:", e)

        return jsonify({
            "success": False,
            "message": "เกิดข้อผิดพลาด",
            "error": str(e)
        }), 500

    finally:

        if cursor is not None:
            cursor.close()

        connection.close()    

# =========================================================
# LOGIN
# =========================================================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "กรุณากรอก Username และ Password"
        }), 400

    connection = get_connection()

    if connection is None:
        return jsonify({
            "success": False,
            "message": "ไม่สามารถเชื่อมต่อ Database ได้"
        }), 500

    try:

        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                name,
                username,
                password,
                image_path
            FROM users
            WHERE username = %s
        """, (username,))

        user = cursor.fetchone()

        if user is None:
            return jsonify({
                "success": False,
                "message": "ไม่พบ Username นี้"
            }), 401

        # ตรวจสอบ Password
        if user["password"] != password:
            return jsonify({
                "success": False,
                "message": "Password ไม่ถูกต้อง"
            }), 401

        return jsonify({
            "success": True,
            "message": "เข้าสู่ระบบสำเร็จ",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "username": user["username"],
                "image_path": user["image_path"]
            }
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "เกิดข้อผิดพลาด",
            "error": str(e)
        }), 500

    finally:

        cursor.close()
        connection.close()


# =========================================================
# GET ALL USERS
# =========================================================

@app.route("/api/users", methods=["GET"])
def get_users():

    connection = get_connection()

    if connection is None:
        return jsonify({
            "success": False,
            "message": "ไม่สามารถเชื่อมต่อ Database ได้"
        }), 500

    try:

        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                name,
                username,
                image_path,
                created_at
            FROM users
            ORDER BY id DESC
        """)

        users = cursor.fetchall()

        return jsonify({
            "success": True,
            "users": users
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "เกิดข้อผิดพลาด",
            "error": str(e)
        }), 500

    finally:

        cursor.close()
        connection.close()


# =========================================================
# GET USER BY ID
# =========================================================

@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):

    connection = get_connection()

    if connection is None:
        return jsonify({
            "success": False,
            "message": "ไม่สามารถเชื่อมต่อ Database ได้"
        }), 500

    try:

        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                name,
                username,
                image_path,
                created_at
            FROM users
            WHERE id = %s
        """, (user_id,))

        user = cursor.fetchone()

        if user is None:
            return jsonify({
                "success": False,
                "message": "ไม่พบผู้ใช้งาน"
            }), 404

        return jsonify({
            "success": True,
            "user": user
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "เกิดข้อผิดพลาด",
            "error": str(e)
        }), 500

    finally:

        cursor.close()
        connection.close()


# =========================================================
# RUN SERVER
# =========================================================

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )