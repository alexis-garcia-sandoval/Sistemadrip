import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sistemadrip-vaporwave-2024-secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///sistemadrip.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Inicia sesión para continuar ✨'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        from models import Usuario
        return db.session.get(Usuario, int(user_id))

    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.cliente import cliente_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(cliente_bp, url_prefix='/tienda')

    @app.context_processor
    def inject_globals():
        carrito_count = 0
        if current_user.is_authenticated and current_user.tipo == 'cliente':
            from models import Carrito
            carrito_count = Carrito.query.filter_by(id_usuario=current_user.id).count()
        return {'carrito_count': carrito_count}

    with app.app_context():
        db.create_all()
        _seed_initial_data()

    return app


def _seed_initial_data():
    from models import Usuario, Producto
    from werkzeug.security import generate_password_hash

    if not Usuario.query.filter_by(tipo='admin').first():
        admin = Usuario(
            nombre='Admin',
            correo='admin@sistemadrip.com',
            contrasena=generate_password_hash('admin123'),
            tipo='admin'
        )
        db.session.add(admin)
        db.session.commit()

    if Producto.query.count() == 0:
        productos_demo = [
            Producto(nombre='Hoodie Neon Dreams', categoria='sueteres', emoji='🧥',
                     precio=850.00, stock=15,
                     descripcion='Hoodie premium con diseño vaporwave neón. 100% algodón.'),
            Producto(nombre='Camiseta Retro Wave', categoria='camisas', emoji='👕',
                     precio=320.00, stock=30,
                     descripcion='Camiseta oversize con estampado retro wave.'),
            Producto(nombre='Gorra Drip Classic', categoria='gorras', emoji='🧢',
                     precio=250.00, stock=20,
                     descripcion='Gorra snapback edición limitada.'),
            Producto(nombre='Joggers Purple Rain', categoria='pantalones', emoji='👖',
                     precio=680.00, stock=10,
                     descripcion='Joggers con detalles en morado.'),
            Producto(nombre='Tenis Cyber Pulse', categoria='tenis', emoji='👟',
                     precio=1200.00, stock=8,
                     descripcion='Tenis chunky estilo Y2K.'),
            Producto(nombre='Collar Pixel Chain', categoria='accesorios', emoji='💍',
                     precio=180.00, stock=25,
                     descripcion='Collar de cadena con pixelado metálico.'),
        ]
        db.session.add_all(productos_demo)
        db.session.commit()


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
