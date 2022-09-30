import os
import time
import io

from pymongo import MongoClient
from flask import Flask, flash, request, redirect, url_for, send_from_directory, send_file
from werkzeug.utils import secure_filename
import magic_classification_machine
import gridfs
# from PIL import Image
# import moto_moto as boto
# from markupsafe import escape

UPLOAD_FOLDER = '/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploads', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        print(file)
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # mongodb here!
            mongo_client = MongoClient("mongodb+srv://BINITAdmin:iNyp7QoHZ5ReLOSk@binit-cluster.tzibqip.mongodb.net/?retryWrites=true&w=majority")
            photo_database = mongo_client['Photo-Database']
            photo_collection = photo_database['Photos']

            # gridfs here!
            fs = gridfs.GridFS(photo_database)

            photo_info = {
                'time': time.gmtime(),
                'classification': magic_classification_machine.classify(file),
                'user': 'unknown',
                'filename': file.filename,
                'file-grid': fs.put(open(file_path, 'rb').read())
            }

            photo_collection.insert_one(photo_info)

            return redirect(url_for('upload_file', name=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/uploads/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    # return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    # mongodb here!
    mongo_client = MongoClient(
        "mongodb+srv://BINITAdmin:iNyp7QoHZ5ReLOSk@binit-cluster.tzibqip.mongodb.net/?retryWrites=true&w=majority")
    photo_database = mongo_client['Photo-Database']
    photo_collection = photo_database['Photos']

    fs = gridfs.GridFS(photo_database)

    file_grid = photo_collection.find({"filename": filename}, {"file-grid": 1})

    # print(file_grid.next())

    if file_grid is None:
        return None

    raw_image = io.BytesIO(fs.get(file_grid.next().get('file-grid')).read())

    return send_file(raw_image, download_name='image.jpg', as_attachment=True)

