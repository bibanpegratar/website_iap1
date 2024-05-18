import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app
)

from hostit.db import get_db
from . import auth
import os
import imghdr
import uuid
from flask import request, session, send_from_directory
from werkzeug.utils import secure_filename

photo_options = {
    "": "Select a photo type",
    "landscape": "Landscape",
    "portrait": "Portrait",
    "natureee": "Natureeee",
    "architecture": "Architecture"
}

bp = Blueprint('blog', __name__, url_prefix='/blog')

@bp.route('/about_me', methods=['GET'])
def about_me():
    return render_template('blog/about_me.html')

# Add a new route to the blog blueprint that will display all images in the database.
@bp.route('/gallery', methods=['GET'])
def gallery():
    db = get_db()
    images = db.execute("SELECT * FROM image").fetchall()
    
    # Group images by their type
    photos_by_type = {}
    for image in images:
        photo_type = image['type']
        if photo_type not in photos_by_type:
            photos_by_type[photo_type] = []
        photos_by_type[photo_type].append(image)
    
    return render_template('/blog/gallery.html', photos_by_type=photos_by_type, photo_options=photo_options)


@bp.route('/post_image', methods=('GET', 'POST'))
def post_image():
    if g.user is None:
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        error = None
        image = request.files['image']
        user_id = session.get('user_id')
        photo_type = request.form['photo_type']
        caption = request.form['caption']
        filename = secure_filename(image.filename)
            
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in current_app.config[
            "UPLOAD_EXTENSIONS"
        ] or file_ext != validate_image(image.stream):
            error = "Invalid image extension"
            
        else:
            # check if filename exists, if so, generate a new filename
            while os.path.exists(os.path.join(current_app.config["UPLOAD_PATH"], filename)):
                filename = str(uuid.uuid4()) + filename
            
            print(filename)
            db = get_db()
            error = None

            if not image:
                error = 'Image is required.'
            
            if not photo_type:
                error = 'Photo type is required.'

            if error is None:
                try:
                    db.execute(
                        "INSERT INTO image (user_id, image, type, caption) VALUES (?, ?, ?, ?)",
                        (user_id, filename, photo_type, caption),
                    )
                    db.commit()
                except db.IntegrityError:
                    error = f"Error posting image"
                else:
                    flash("Image posted successfully")
                    image.save(os.path.join(current_app.config["UPLOAD_PATH"], filename))
                    return redirect(url_for("blog.post_image"))
                
        flash(error)
    return render_template('blog/post_image.html', photo_options=photo_options)

def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return "." + (format if format != "jpeg" else "jpg")

@bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_PATH'], filename)
