from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev'

    from . import routes
    app.register_blueprint(routes.bp)

    return app
