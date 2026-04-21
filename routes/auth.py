from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from models import Usuario

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.tipo == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('cliente.tienda'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        correo = request.form.get('correo', '').strip()
        contrasena = request.form.get('contrasena', '')
        usuario = Usuario.query.filter_by(correo=correo).first()

        if usuario and check_password_hash(usuario.contrasena, contrasena):
            login_user(usuario)
            flash(f'¡Bienvenid@ {usuario.nombre}! 🔥', 'success')
            if usuario.tipo == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('cliente.tienda'))

        flash('Correo o contraseña incorrectos ❌', 'danger')

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        correo = request.form.get('correo', '').strip()
        contrasena = request.form.get('contrasena', '')
        confirmar = request.form.get('confirmar', '')

        if contrasena != confirmar:
            flash('Las contraseñas no coinciden ❌', 'danger')
            return render_template('register.html')

        if Usuario.query.filter_by(correo=correo).first():
            flash('Este correo ya está registrado ❌', 'danger')
            return render_template('register.html')

        usuario = Usuario(
            nombre=nombre,
            correo=correo,
            contrasena=generate_password_hash(contrasena),
            tipo='cliente'
        )
        db.session.add(usuario)
        db.session.commit()

        login_user(usuario)
        flash(f'¡Cuenta creada! Bienvenid@ {nombre} 🎉', 'success')
        return redirect(url_for('cliente.tienda'))

    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada 👋', 'info')
    return redirect(url_for('auth.login'))
