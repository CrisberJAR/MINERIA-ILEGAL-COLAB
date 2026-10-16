from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
import bcrypt
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.utils import load_img, img_to_array

app = Flask(__name__)
app.secret_key = 'clave_secreta_mineria_ilegal'

# Conexión a MongoDB Atlas
MONGO_URI = 'mongodb+srv://crisberjosepambichoreynoso_db_user:Alhis_123@cluster0.hbqoiwt.mongodb.net/mineria_ilegal?retryWrites=true&w=majority'
client = MongoClient(MONGO_URI)
db = client['mineria_ilegal']
users_collection = db['users']

# Construir la estructura exacta del modelo y cargar solo los pesos (100% compatible en Render)
model = models.Sequential([
    layers.Rescaling(1./255, input_shape=(150, 150, 3)),
    layers.Conv2D(16, 3, padding='same', activation='relu'),
    layers.MaxPooling2D(),
    layers.Conv2D(32, 3, padding='same', activation='relu'),
    layers.MaxPooling2D(),
    layers.Flatten(),
    layers.Dense(64, activation='relu'),
    layers.Dense(1, activation='sigmoid')
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

MODEL_PATH = 'modelo_mineria.h5'
if os.path.exists(MODEL_PATH):
    try:
        model.load_weights(MODEL_PATH)
        print("Pesos del modelo cargados exitosamente.")
    except Exception as e:
        print(f"Error al cargar los pesos del modelo: {e}")
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
        
        if users_collection.find_one({'username': username}):
            return render_template('register.html', error="El usuario ya existe.")
        
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
            return render_template('login.html', error="Credenciales incorrectas.")
            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/entrenar', methods=['POST'])
def entrenar():
    if 'username' not in session:
        return redirect(url_for('login'))
    mensaje = "Nota: El entrenamiento del modelo se ejecuta directamente desde la terminal de Google Colab por requerimiento académico."
    return render_template('dashboard.html', username=session['username'], resultado_entreno=mensaje)

@app.route('/detectar', methods=['POST'])
def detectar():
    if 'username' not in session:
        return redirect(url_for('login'))

    if 'imagen_satelital' not in request.files:
        return render_template('dashboard.html', username=session['username'], resultado="No se seleccionó ningún archivo.", tipo_alerta="danger")

    file = request.files['imagen_satelital']
    if file.filename == '':
        return render_template('dashboard.html', username=session['username'], resultado="No se seleccionó ninguna imagen.", tipo_alerta="danger")

    if file:
        temp_path = 'temp_image.jpg'
        file.save(temp_path)

        # Preprocesamiento de la imagen
        img = load_img(temp_path, target_size=(150, 150))
        img_array = img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        # Inferencia con el modelo
        prediction = model.predict(img_array)[0][0]
        
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if prediction > 0.5:
            resultado = f"Alerta: Indicios de Mineria Ilegal Detectados (Nivel de Confianza: {prediction*100:.2f}%)"
            tipo_alerta = "danger"
        else:
            resultado = f"Resultado: Area Normal / Sin Indicios de Mineria Ilegal (Nivel de Confianza: {(1-prediction)*100:.2f}%)"
            tipo_alerta = "success"

        return render_template('dashboard.html', username=session['username'], resultado=resultado, tipo_alerta=tipo_alerta)
    
    return render_template('dashboard.html', username=session['username'], resultado="Error al procesar la imagen.", tipo_alerta="danger")

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)