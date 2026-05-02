import os

from flask import Flask
from flask_cors import CORS

from config import Config
from extensions import bcrypt, db, jwt
from routes.auth_routes import auth_bp
from routes.opportunity_routes import opportunity_bp


def create_app():
    basedir = os.path.abspath(os.path.dirname(__file__))
    sky_folder = os.path.abspath(os.path.join(basedir, '..', 'sky'))

    app = Flask(__name__, static_folder=sky_folder, static_url_path='')
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(opportunity_bp)

    with app.app_context():
        db.create_all()

    @app.route('/')
    def index():
        return app.send_static_file('admin.html')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
