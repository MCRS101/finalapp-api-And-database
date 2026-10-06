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

    username = data.get("username")
    password = data.get("password")

    print("====================================")
    print("LOGIN")
    print("Username:", username)
    print("====================================")

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

    cursor = None

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

        # ไม่พบ Username
        if user is None:
            return jsonify({
                "success": False,
                "message": "ไม่พบ Username นี้"
            }), 401

        # Password ไม่ถูกต้อง
        if user["password"] != password:
            return jsonify({
                "success": False,
                "message": "Password ไม่ถูกต้อง"
            }), 401

        print("LOGIN SUCCESS:", user["id"])

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

        print("LOGIN ERROR:", e)

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
# HOUSEHOLD
# =========================================================


# =========================================================
# GET ALL HOUSEHOLDS
# =========================================================

@app.route("/api/households", methods=["GET"])
def get_households():

    connection = get_connection()

    if connection is None:
        return jsonify({
            "success": False,
            "message": "ไม่สามารถเชื่อมต่อ Database ได้"
        }), 500

    cursor = None

    try:

        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                house_number,
                moo,
                village,
                subdistrict,
                district,
                province,
                owner_name,
                latitude,
                longitude,
                image_path,
                created_at
            FROM households
            ORDER BY id DESC
        """)

        households = cursor.fetchall()

        return jsonify({
            "success": True,
            "households": households
        }), 200

    except Exception as e:

        print("GET HOUSEHOLDS ERROR:", e)

        return jsonify({
            "success": False,
            "message": "ไม่สามารถโหลดข้อมูลครัวเรือนได้",
            "error": str(e)
        }), 500

    finally:

        if cursor is not None:
            cursor.close()

        connection.close()


# =========================================================
# GET HOUSEHOLD BY ID
# =========================================================

@app.route("/api/households/<int:house_id>", methods=["GET"])
def get_household(house_id):

    connection = get_connection()

    if connection is None:
        return jsonify({
            "success": False,
            "message": "ไม่สามารถเชื่อมต่อ Database ได้"
        }), 500

    cursor = None

    try:

        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                house_number,
                moo,
                village,
                subdistrict,
                district,
                province,
                owner_name,
                latitude,
                longitude,
                image_path,
                created_at
            FROM households
            WHERE id = %s
        """, (house_id,))

        household = cursor.fetchone()

        if household is None:
            return jsonify({
                "success": False,
                "message": "ไม่พบข้อมูลครัวเรือน"
            }), 404

        return jsonify({
            "success": True,
            "household": household
        }), 200

    except Exception as e:

        print("GET HOUSEHOLD ERROR:", e)

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
# ADD HOUSEHOLD
# =========================================================

@app.route('/api/households', methods=['POST'])
def add_household():

    try:
        house_number = request.form.get('house_number')
        moo = request.form.get('moo')
        village = request.form.get('village')
        subdistrict = request.form.get('subdistrict')
        district = request.form.get('district')
        province = request.form.get('province')
        owner_name = request.form.get('owner_name')

        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        image = request.files.get('image')

        print('====================================')
        print('ADD HOUSEHOLD')
        print('house_number:', house_number)
        print('moo:', moo)
        print('village:', village)
        print('subdistrict:', subdistrict)
        print('district:', district)
        print('province:', province)
        print('owner_name:', owner_name)
        print('latitude:', latitude)
        print('longitude:', longitude)
        print('image:', image)
        print('====================================')

        # -----------------------------
        # ตรวจสอบข้อมูล
        # -----------------------------

        if not house_number:
            return jsonify({
                'success': False,
                'message': 'กรุณากรอกบ้านเลขที่'
            }), 400

        if not latitude or not longitude:
            return jsonify({
                'success': False,
                'message': 'กรุณาระบุพิกัด'
            }), 400

        if image is None:
            return jsonify({
                'success': False,
                'message': 'กรุณาเพิ่มรูปครัวเรือน'
            }), 400

        # -----------------------------
        # Upload รูปไป Cloudinary
        # -----------------------------

        upload_result = upload_image(image)

        image_path = upload_result['image_url']

        print('Cloudinary URL:', image_path)

        # -----------------------------
        # Database
        # -----------------------------

        connection = get_connection()

        if connection is None:
            return jsonify({
                'success': False,
                'message': 'ไม่สามารถเชื่อมต่อ Database'
            }), 500

        cursor = connection.cursor()

        sql = """
            INSERT INTO households (
                house_number,
                moo,
                village,
                subdistrict,
                district,
                province,
                owner_name,
                latitude,
                longitude,
                image_path
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
        """

        values = (
            house_number,
            moo,
            village,
            subdistrict,
            district,
            province,
            owner_name,
            float(latitude),
            float(longitude),
            image_path,
        )

        cursor.execute(sql, values)

        connection.commit()

        house_id = cursor.lastrowid

        cursor.close()
        connection.close()

        print('HOUSEHOLD INSERT SUCCESS')
        print('ID:', house_id)

        return jsonify({
            'success': True,
            'message': 'เพิ่มข้อมูลครัวเรือนสำเร็จ',
            'id': house_id,
            'image_path': image_path
        }), 201

    except Exception as e:

        print('====================================')
        print('ADD HOUSEHOLD ERRORR')
        print(e)
        print('====================================')

        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# =========================================================
# UPDATE HOUSEHOLD
# =========================================================

@app.route('/api/households/<int:id>', methods=['PUT'])
def update_household(id):

    try:
        house_number = request.form.get(
            'house_number'
        )

        moo = request.form.get('moo')

        village = request.form.get(
            'village'
        )

        subdistrict = request.form.get(
            'subdistrict'
        )

        district = request.form.get(
            'district'
        )

        province = request.form.get(
            'province'
        )

        owner_name = request.form.get(
            'owner_name'
        )

        latitude = request.form.get(
            'latitude'
        )

        longitude = request.form.get(
            'longitude'
        )

        # รูปใหม่ ถ้ามี
        image = request.files.get(
            'image'
        )

        connection = get_connection()

        if connection is None:
            return jsonify({
                'success': False,
                'message':
                    'ไม่สามารถเชื่อมต่อ Database'
            }), 500

        cursor = connection.cursor()

        # =====================================================
        # ถ้ามีรูปใหม่
        # =====================================================

        if image is not None:

            upload_result = upload_image(
                image,
                folder='final_app/households'
            )

            image_path = upload_result[
                'image_url'
            ]

            sql = """
                UPDATE households
                SET
                    house_number = %s,
                    moo = %s,
                    village = %s,
                    subdistrict = %s,
                    district = %s,
                    province = %s,
                    owner_name = %s,
                    latitude = %s,
                    longitude = %s,
                    image_path = %s
                WHERE id = %s
            """

            values = (
                house_number,
                moo,
                village,
                subdistrict,
                district,
                province,
                owner_name,
                float(latitude),
                float(longitude),
                image_path,
                id
            )

        # =====================================================
        # ไม่มีรูปใหม่ → ใช้รูปเดิม
        # =====================================================

        else:

            sql = """
                UPDATE households
                SET
                    house_number = %s,
                    moo = %s,
                    village = %s,
                    subdistrict = %s,
                    district = %s,
                    province = %s,
                    owner_name = %s,
                    latitude = %s,
                    longitude = %s
                WHERE id = %s
            """

            values = (
                house_number,
                moo,
                village,
                subdistrict,
                district,
                province,
                owner_name,
                float(latitude),
                float(longitude),
                id
            )

        cursor.execute(
            sql,
            values
        )

        connection.commit()

        if cursor.rowcount == 0:

            cursor.close()
            connection.close()

            return jsonify({
                'success': False,
                'message':
                    'ไม่พบข้อมูลครัวเรือน'
            }), 404

        cursor.close()
        connection.close()

        return jsonify({
            'success': True,
            'message':
                'แก้ไขข้อมูลครัวเรือนสำเร็จ'
        })

    except Exception as e:

        print(
            'UPDATE HOUSEHOLD ERROR:',
            e
        )

        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# =========================================================
# DELETE HOUSEHOLD
# =========================================================

@app.route("/api/households/<int:house_id>", methods=["DELETE"])
def delete_household(house_id):

    connection = get_connection()

    if connection is None:
        return jsonify({
            "success": False,
            "message": "ไม่สามารถเชื่อมต่อ Database ได้"
        }), 500

    cursor = None

    try:

        cursor = connection.cursor()

        # =================================================
        # CHECK HOUSEHOLD
        # =================================================

        cursor.execute(
            "SELECT id FROM households WHERE id = %s",
            (house_id,)
        )

        existing = cursor.fetchone()

        if existing is None:
            return jsonify({
                "success": False,
                "message": "ไม่พบข้อมูลครัวเรือน"
            }), 404

        # =================================================
        # DELETE
        # =================================================

        cursor.execute(
            "DELETE FROM households WHERE id = %s",
            (house_id,)
        )

        connection.commit()

        print("DELETE HOUSEHOLD SUCCESS:", house_id)

        return jsonify({
            "success": True,
            "message": "ลบข้อมูลครัวเรือนสำเร็จ"
        }), 200

    except Exception as e:

        connection.rollback()

        print("DELETE HOUSEHOLD ERROR:", e)

        return jsonify({
            "success": False,
            "message": "ไม่สามารถลบข้อมูลครัวเรือนได้",
            "error": str(e)
        }), 500

    finally:

        if cursor is not None:
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