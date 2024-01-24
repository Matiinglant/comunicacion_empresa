from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from datetime import datetime
import pytz  # Importa la librería pytz
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta'  # Cambia esto por una clave segura y única
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'site.db')
socketio = SocketIO(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)

# Configuración básica de usuario para propósitos de ejemplo
class User(UserMixin):
    def __init__(self, user_id, username, password):
        self.id = user_id
        self.username = username
        self.password = password

# Configuración del manejador de carga de usuario
@login_manager.user_loader
def load_user(user_id):
    return User(user_id, '', '')  # Debes personalizar esto según tu sistema de usuarios

# Definición del modelo de mensajes
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

def create_app():
    # Función para crear la aplicación Flask
    return app

def init_db():
    # Función para inicializar la base de datos
    with app.app_context():
        db.create_all()

def get_all_messages():
    # Función para obtener todos los mensajes de la base de datos
    return Message.query.all()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        user = User(user_id, '', '')  # Debes personalizar esto según tu sistema de usuarios
        login_user(user)
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    # Obtener todos los mensajes de la base de datos
    messages = get_all_messages()
    return render_template('index.html', messages=messages)

@socketio.on('message')
def handle_message(message):
    user_id = current_user.id if current_user.is_authenticated else 'Anónimo'
    
    # Obtener la hora actual en la zona horaria de Argentina
    tz = pytz.timezone('America/Argentina/Buenos_Aires')
    timestamp = datetime.now(tz)

    # Guardar el mensaje en la base de datos
    new_message = Message(user_id=user_id, content=message, timestamp=timestamp)
    db.session.add(new_message)
    db.session.commit()

    # Emitir el mensaje a todos los clientes
    emit('message', {'user': user_id, 'message': message, 'time': timestamp.strftime('%H:%M')}, broadcast=True)

@socketio.on('connect')
def handle_connect():
    # Enviar los mensajes existentes al cliente recién conectado
    messages = get_all_messages()
    for message in messages:
        emit('message', {'user': message.user_id, 'message': message.content, 'time': message.timestamp.strftime('%H:%M')})

if __name__ == '__main__':
    init_db()  # Inicializa la base de datos al ejecutar el script
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

