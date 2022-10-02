import os
import time
import io

import mysql.connector
import mysqlx.helpers
from pymongo import MongoClient
from flask import Flask, flash, request, redirect, url_for, send_from_directory, send_file
from werkzeug.utils import secure_filename
import magic_classification_machine
import gridfs
# from PIL import Image
# import moto_moto as boto
# from markupsafe import escape

UPLOAD_FOLDER = '\\uploads\\unclassified'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def classification_to_int(classification_string):
    if classification_string == "Trash":
        return 0
    elif classification_string == "Recycle":
        return 1
    elif classification_string == "Compost":
        return 2
    else:
        return -1


def mysql_connect():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="12lego34",
        database="binit"
    )
    return mydb


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def db_test():
    db = mysql_connect()
    cursor = db.cursor()

    sql = "INSERT INTO photos " \
          "(date, user, machine_classification, path) VALUES " \
          "(%s, %s, %s, %s)"
    val = (time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()), "admin", 1, "C:/uploads/unclassified/photo.jpg")
    cursor.execute(sql, val)

    #db.commit()

    print(cursor.execute("SELECT * FROM photos"))

    return 'database test'


@app.route('/upload/<path:username>', methods=['GET', 'POST'])
def upload_file(username):
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
            file.filename = username + '_' + timestamp + '.' + file.filename.rsplit('.', 1)[1].lower()
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            classification = magic_classification_machine.classify(file)

            db = mysql_connect()
            cursor = db.cursor()
            sql = "INSERT INTO photos " \
                  "(date, user, machine_classification, path, name) VALUES " \
                  "(%s, %s, %s, %s, %s)"
            val = (timestamp,
                   username,
                   classification_to_int(classification),
                   file_path,
                   filename)
            try:
                cursor.execute(sql, val)
            except mysql.connector.errors.IntegrityError:
                return 'duplicate name'
            db.commit()

            # # mongodb here!
            # mongo_client = MongoClient("mongodb+srv://BINITAdmin:iNyp7QoHZ5ReLOSk@binit-cluster.tzibqip.mongodb.net/?retryWrites=true&w=majority")
            # photo_database = mongo_client['Photo-Database']
            # photo_collection = photo_database['Photos']
            #
            # # gridfs here!
            # fs = gridfs.GridFS(photo_database)
            #
            # photo_info = {
            #     'time': time.gmtime(),
            #     'classification': magic_classification_machine.classify(file),
            #     'user': 'unknown',
            #     'filename': file.filename,
            #     'file-grid': fs.put(open(file_path, 'rb').read())
            # }
            #
            # photo_collection.insert_one(photo_info)

            return classification
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/list_unclassified/<path:username>', methods=['GET'])
def list_unclassified(username):

    db = mysql_connect()
    cursor = db.cursor()
    sql = "SELECT id, name FROM photos WHERE user='" + username + "' AND user_classification=-1"
    cursor.execute(sql)
    paths = cursor.fetchall()
    # print(paths)
    return paths


@app.route('/download_by_name/<path:filename>', methods=['GET'])
def download_by_path(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/download_by_id/<path:photo_id>', methods=['GET'])
def download_by_id(photo_id):
    db = mysql_connect()
    cursor = db.cursor()
    sql = "SELECT name FROM photos WHERE id=" +  photo_id
    cursor.execute(sql)
    filename = cursor.fetchone()[0]
    print(filename)
    if filename is None:
        filename = ""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # # mongodb here!
    # mongo_client = MongoClient(
    #     "mongodb+srv://BINITAdmin:iNyp7QoHZ5ReLOSk@binit-cluster.tzibqip.mongodb.net/?retryWrites=true&w=majority")
    # photo_database = mongo_client['Photo-Database']
    # photo_collection = photo_database['Photos']
    #
    # fs = gridfs.GridFS(photo_database)
    #
    # file_grid = photo_collection.find({"filename": filename}, {"file-grid": 1})
    #
    # # print(file_grid.next())
    #
    # if file_grid is None:
    #     return None
    #
    # raw_image = io.BytesIO(fs.get(file_grid.next().get('file-grid')).read())
    #
    # return send_file(raw_image, download_name='image.jpg', as_attachment=True)

