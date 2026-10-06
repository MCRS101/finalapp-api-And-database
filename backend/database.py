import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )

        return connection

    except Error as e:
        print("MySQL connection error:", e)
        return None


def init_database():
    connection = get_connection()

    if connection is None:
        print("Cannot connect to MySQL")
        return

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            username VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            image_path VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS households (
            id INT AUTO_INCREMENT PRIMARY KEY,
            house_number VARCHAR(50) NOT NULL,
            moo VARCHAR(50),
            village VARCHAR(255),
            subdistrict VARCHAR(255),
            district VARCHAR(255),
            province VARCHAR(255),
            owner_name VARCHAR(255),
            latitude DOUBLE NOT NULL,
            longitude DOUBLE NOT NULL,
            image_path VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    cursor.close()
    connection.close()

    print("Database initialized successfully")