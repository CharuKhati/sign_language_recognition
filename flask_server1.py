from flask import Flask, request, jsonify
import sqlite3
import os
import subprocess
import logging
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Database initialization
DATABASE = "user_data.db"

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("PRAGMA journal_mode = WAL;")  # Set Write-Ahead Logging mode
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            name TEXT NOT NULL,
                            dob TEXT NOT NULL,
                            gender TEXT NOT NULL,
                            phone TEXT NOT NULL,
                            email TEXT UNIQUE NOT NULL,
                            role TEXT NOT NULL,
                            password TEXT NOT NULL
                          )''')
        conn.commit()

init_db()

# Endpoint to handle signup
@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        logging.info(f"Received signup data: {data}")  # Debug logging
        
        # Validate received data
        required_fields = ['username', 'name', 'dob', 'gender', 'phone', 'email', 'role', 'password']
        if not all(field in data and data[field] for field in required_fields):
            return jsonify({"message": "All fields are required"}), 400

        # Insert into database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, name, dob, gender, phone, email, role, password)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['username'], data['name'], data['dob'], data['gender'],
            data['phone'], data['email'], data['role'], data['password']
        ))
        conn.commit()
        conn.close()

        logging.info("User successfully registered in the database")
        return jsonify({"message": "Signup successful"}), 200
    except sqlite3.IntegrityError as e:
        logging.error(f"Integrity error: {e}")
        return jsonify({"message": "Username or email already exists"}), 400
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"message": f"Server error: {str(e)}"}), 500


# Endpoint to handle login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, role FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()

        if user:
            return jsonify({"message": "Login successful", "name": user[0], "role": user[1]}), 200
        else:
            return jsonify({"error": "Invalid username or password"}), 401

# Endpoint to recognize signs
@app.route('/recognize', methods=['POST'])
def recognize_signs():
    try:
        # Get the absolute path of the script
        script_path = os.path.join(os.getcwd(), "app.py")  # Adjust this if your app.py is in a different location
        
        # Specify the Python executable to use (ensure it matches your virtual environment)
        venv_python = os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")  # Update with the correct path if needed

        logging.info(f"Executing script with Python: {venv_python} at {script_path}")
        
        # Run the script using subprocess
        result = subprocess.run([venv_python, script_path], capture_output=True, text=True, check=True)

        # Log the standard output of the script
        logging.info(f"Script output: {result.stdout}")

        # If the script ran successfully, send a success response
        return jsonify({"message": "Recognize Signs script executed successfully!"}), 200

    except subprocess.CalledProcessError as e:
        # Log the error if the script fails
        logging.error(f"Error during recognition: {e}")
        logging.error(f"stderr: {e.stderr}")

        # Return an error response with the details of the failure
        return jsonify({"error": "Failed to execute recognize script", "details": e.stderr}), 500

    except Exception as e:
        # Catch any other exceptions
        logging.error(f"Unexpected error: {e}")
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500



# Endpoint to collect data
@app.route('/collect', methods=['POST'])
def collect_data():
    try:
        # Get the absolute path of the collect_data.py script
        script_path = os.path.join(os.getcwd(), "collect_data.py")  # Adjust path if necessary

        # Specify the Python executable to use (ensure it matches your virtual environment)
        venv_python = os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")  # Update with the correct path if needed

        logging.info(f"Executing script with Python: {venv_python} at {script_path}")

        # Run the script using subprocess
        result = subprocess.run([venv_python, script_path], capture_output=True, text=True, check=True)

        # Log the standard output of the script
        logging.info(f"Script output: {result.stdout}")

        # If the script ran successfully, send a success response
        return jsonify({"message": "Collect Data script executed successfully!"}), 200

    except subprocess.CalledProcessError as e:
        # Log the error if the script fails
        logging.error(f"Error during data collection: {e}")
        logging.error(f"stderr: {e.stderr}")

        # Return an error response with the details of the failure
        return jsonify({"error": "Failed to execute collect script", "details": e.stderr}), 500

    except Exception as e:
        # Catch any other exceptions
        logging.error(f"Unexpected error: {e}")
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


# Run the Flask app
if __name__ == '__main__':
    debug_mode = os.getenv("DEBUG", "True") == "True"
    app.run(debug=debug_mode, host="0.0.0.0", port=5000)
