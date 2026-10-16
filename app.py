from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
import bcrypt
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image

app = Flask(__name__)
app.secret_key = 'clave_secreta_mineria_ilegal'

# Conexión directa a MongoDB Atlas especificando la base de datos mineria_ilegal
MONGO_URI = 'mongodb+srv://crisberjosepambichoreynoso_db_user:Alhis_123@cluster0.hbqoiwt.mongodb.net/mineria_ilegal?retryWrites=true&w=majority'
client = MongoClient(MONGO_URI)

# Base de datos y colección 'users' donde se guardarán los registros
db = client['mineria_ilegal']
users_collection = db['users']

# Cargar el modelo preentrenado de TensorFlow
MODEL_PATH = 'modelo_mineria.h5'
model = None

if os.path.exists(MODEL_PATH):
    try:
        model = tf.keras.models.load_model(MODEL_PATH)
        print("Modelo cargado exitosamente.")
    except Exception as e:
        print(f"Error al cargar el modelo: {e}")
else:
    print(f"Advertencia: No se encontró el archivo {MODEL_PATH}")

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
        
        # Verificar si el usuario ya existe en MongoDB
        if users_collection.find_one({'username': username}):
            return "El usuario ya existe. <a href='/register'>Intentar de nuevo</a>"
        
        # Guardar el nuevo usuario en la colección 'users'
        users_collection.insert_one({
            'username': username,
            'password': hashed_password
        })
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        user = users_collection.find_one({'username': username})
        
        if user and bcrypt.checkpw(password, user['password']):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return "Credenciales incorrectas. <a href='/login'>Intentar de nuevo</a>"
            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/detectar', methods=['POST'])
def detectar():
    if 'username' not in session:
        return redirect(url_for('login'))

    if 'imagen' not in request.files:
        return render_template('dashboard.html', username=session['username'], resultado="No se seleccionó ningún archivo.")

    file = request.files['imagen']
    if file.filename == '':
        return render_template('dashboard.html', username=session['username'], resultado="No se seleccionó ninguna imagen.")

    if file and model:
        # Guardar imagen temporalmente
        temp_path = os.path.join('temp_image.jpg')
        file.save(temp_path)

        # Preprocesar la imagen
        img = image.load_img(temp_path, target_size=(150, 150))
        img_array = image.img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        # Predicción
        prediction = model.predict(img_array)[0][0]
        
        # Limpiar archivo temporal
        if os.path.exists(temp_path):
            os.remove(temp_path)

        # Determinar resultado
        if prediction > 0.5:
            resultado = f"Detección de Minería Ilegal Detectada (Confianza: {prediction*100:.2f}%)"
        else:
            resultado = f"Área Normal / Sin Minería Ilegal (Confianza: {(1-prediction)*100:.2f}%)"

        return render_template('dashboard.html', username=session['username'], resultado=resultado)
    
    return render_template('dashboard.html', username=session['username'], resultado="El modelo no está cargado correctamente.")

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)