import os
import io
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from database import execute_query
from dataset_processor import process_and_clean_file
from ai_service import generate_full_report, generate_chat_response

app = Flask(__name__)
app.secret_key = "super_secret_key_v2_btech"
UPLOAD_FOLDER = '/tmp/uploads' if os.environ.get('VERCEL') else os.path.join(os.path.dirname(__file__), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- AUTH ROUTES ---

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session.get('username'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = execute_query('SELECT * FROM users WHERE username = ?', (username,), fetchone=True)
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            error = 'Invalid credentials. Please try again.'
            
    return render_template('auth.html', error=error, mode='login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = execute_query('SELECT * FROM users WHERE username = ?', (username,), fetchone=True)
        
        if user:
            error = 'User already exists.'
        else:
            execute_query('INSERT INTO users (username, password) VALUES (?, ?)', 
                         (username, generate_password_hash(password)), commit=True)
            return redirect(url_for('login'))
            
    return render_template('auth.html', error=error, mode='register')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# --- API ROUTES ---

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
         return jsonify({"error": "Unauthorized"}), 401
         
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file and (file.filename.endswith('.csv') or file.filename.endswith('.json')):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Process Data - Handles robust errors
            df = process_and_clean_file(filepath)
            
            # Generate Full AI Insights Report
            full_report = generate_full_report(df)
            
            # Save to Database under user id
            dataset_id = execute_query('''
                INSERT INTO datasets (user_id, filename, filepath, summary)
                VALUES (?, ?, ?, ?)
            ''', (session['user_id'], filename, filepath, full_report), commit=True)
            
            # Save context into session
            session['dataset_id'] = dataset_id
            
            # Sending UI data
            nc = list(df.select_dtypes(include=['number']).columns)
            cc = list(df.select_dtypes(exclude=['number']).columns)
            
            chart_data = {
                "columns": list(df.columns),
                "numeric": nc,
                "categorical": cc,
                "preview": df.head(50).to_dict(orient='records')
            }
            
            return jsonify({
                "message": "Upload successful",
                "dataset_id": dataset_id,
                "summary": full_report,
                "chart_data": chart_data
            }), 200
        except ValueError as ve:
             # Our custom data structural errors
             return jsonify({"error": str(ve)}), 400
        except Exception as e:
            return jsonify({"error": "A server error occurred processing this dataset."}), 500
            
    return jsonify({"error": "Only CSV and JSON allowed"}), 400


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get("message", "")
    dataset_id = session.get('dataset_id')
    
    if not dataset_id:
        return jsonify({"response": "Please upload a dataset first."})
        
    dataset = execute_query('SELECT filepath FROM datasets WHERE id = ?', (dataset_id,), fetchone=True)
    
    if not dataset:
        return jsonify({"response": "Dataset not found."})
        
    filepath = dataset['filepath']
    try:
        df = process_and_clean_file(filepath)
        ai_response = generate_chat_response(message, df)
    except Exception as e:
        ai_response = f"Error processing query."
        
    return jsonify({"response": ai_response})

@app.route('/api/history', methods=['GET'])
def get_history():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    datasets = execute_query('SELECT id, filename, upload_date FROM datasets WHERE user_id = ? ORDER BY upload_date DESC', 
                            (session['user_id'],), fetchall=True)
    
    res = [{"id": d["id"], "filename": d["filename"], "upload_date": d["upload_date"]} for d in datasets]
    return jsonify(res)


@app.route('/api/load/<int:ds_id>', methods=['GET'])
def load_historical(ds_id):
    """ Loads an old dataset for viewing """
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    dataset = execute_query('SELECT * FROM datasets WHERE id = ? AND user_id = ?', (ds_id, session['user_id']), fetchone=True)
    
    if not dataset:
         return jsonify({"error": "Dataset not found"}), 404
         
    try:
         df = process_and_clean_file(dataset['filepath'])
         session['dataset_id'] = ds_id
         
         nc = list(df.select_dtypes(include=['number']).columns)
         cc = list(df.select_dtypes(exclude=['number']).columns)
            
         chart_data = {
             "columns": list(df.columns),
             "numeric": nc,
             "categorical": cc,
             "preview": df.head(50).to_dict(orient='records')
         }
            
         return jsonify({
             "message": "Loaded",
             "dataset_id": ds_id,
             "summary": dataset['summary'],
             "chart_data": chart_data
         }), 200
    except Exception as e:
         return jsonify({"error": str(e)}), 400

@app.route('/api/download_clean/<int:ds_id>', methods=['GET'])
def download_clean(ds_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    dataset = execute_query('SELECT filepath, filename FROM datasets WHERE id = ? AND user_id = ?', (ds_id, session['user_id']), fetchone=True)
    
    if not dataset:
        return jsonify({"error": "Dataset not found"}), 404
        
    try:
        df = process_and_clean_file(dataset['filepath'])
        csv_data = df.to_csv(index=False)
        
        return send_file(
            io.BytesIO(csv_data.encode('utf-8')),
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"cleaned_{dataset['filename']}"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
