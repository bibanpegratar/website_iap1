import os
from flask import Flask, request, render_template

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'hostit.sqlite'),
    )
    
    app.config["UPLOAD_EXTENSIONS"] = [".jpg", ".png", ".jpeg"]
    app.config["UPLOAD_PATH"] = os.path.join(app.static_folder, "image_uploads")
    app.config["LOW_RES_PATH"] = os.path.join(app.static_folder, "low_res_uploads")

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
        os.makedirs(app.config['UPLOAD_PATH'])
        os.makedirs(app.config['LOW_RES_PATH'])
    except OSError:
        pass
    
    # expose the app to work with machine outside dokcker
    from . import db
    db.init_app(app)
    
    from . import auth, blog
    app.register_blueprint(auth.bp)
    app.register_blueprint(blog.bp)
    
    @app.route('/')
    def hello():
        if request.method == 'GET':
            return blog.gallery()

    return app