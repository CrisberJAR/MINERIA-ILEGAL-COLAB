from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
import bcrypt

app = Flask(__name__)
app.secret_key = 'clave_secreta_mineria_ilegal'

# Conexión directa a MongoDB Atlas especificando la base de datos mineria_ilegal
MONGO_URI = 'mongodb+srv://crisberjosepambichoreynoso_db_user:Alhis_123@cluster0.hbqoiwt.mongodb.net/mineria_ilegal?retryWrites=true&w=majority'
client = MongoClient(MONGO_URI)

# Base de datos y colección 'users' donde se guardarán los registros
db = client['mineria_ilegal']
users_collection = db['users']

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

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)