import os
import time
import subprocess
import datetime
import io

import mysql.connector
from flask import Flask, flash, request, redirect, url_for, send_from_directory, send_file, jsonify
from werkzeug.utils import secure_filename
import magic_classification_machine

# from PIL import Image
# import moto_moto as boto
# from markupsafe import escape

UPLOAD_FOLDER = '/home/ubuntu/uploads/Unclassified'
BASE_FOLDER = '/home/ubuntu/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

app = Flask(__name__)
# app.run('0.0.0.0', debug=True, port=8000, ssl_context='adhoc')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def classification_to_int(classification_string):
    if classification_string == "trash":
        return 0
    elif classification_string == "paper":
        return 1
    elif classification_string == "cardboard":
        return 2
    elif classification_string == "glass":
        return 3
    elif classification_string == "plastic":
        return 4
    elif classification_string == "metal":
        return 5
    else:
        return -1


def int_to_classification(class_int):
    if class_int == -1:
        return "DELETE"
    elif class_int == 0:
        return "trash"
    elif class_int == 1:
        return "paper"
    elif class_int == 2:
        return "cardboard"
    elif class_int == 3:
        return "glass"
    elif class_int == 4:
        return "plastic"
    elif class_int == 5:
        return "metal"
    else:
        return "Unclassified"


def mysql_connect():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="BINIT_Password",
        database="binit"
    )
    return mydb


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def db_test():
    process = subprocess.run(["dir", ""], shell=True, capture_output=True, universal_newlines=True)
    return_data = {
        "data": "hello world",
        "stdout": process.stdout
    }
    return jsonify(return_data)


@app.route('/upload/<path:device_id>', methods=['GET', 'POST'])
def upload_file(device_id):
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
            db = mysql_connect()
            cursor = db.cursor()

            sql = "SELECT username FROM users WHERE device_id=%s"
            cursor.execute(sql, [device_id])
            try:
                username = cursor.fetchone()[0]
            except TypeError:
                return {"error": "There is no user associated with that device id"}

            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
            file.filename = username + '_' + timestamp + '.' + file.filename.rsplit('.', 1)[1].lower()
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            print("===== checkpoint 1 =====")

            # process = subprocess.run(['echo', 'the pain train'], stdout=subprocess.PIPE, universal_newlines=True)
            # print(process)

            cmd = ["python3",
                   "/home/ubuntu/RecycleNet/webcam.py",
                   "--resume /home/ubuntu/RecycleNet/save/model_best.pth.tar",
                   "--save_dir",
                   file_path,
                   "--resize_needed",
                   "True"]
            print(cmd)
            print(os.environ)
            process = subprocess.run(cmd, capture_output=True, env=os.environ, text=True)

            process_output = process.stdout
            process_error = process.stderr
            print(process_output)
            print(process_error)
            try:
                prediction = process_output.rsplit('\n', 1)[1].split(',')[0].split(' ')[1]
            except IndexError:
                return {"error": "The pain train"}
            # classification = magic_classification_machine.classify(file)

            sql = "INSERT INTO photos " \
                  "(create_date, username, machine_classification, path, filename) VALUES " \
                  "(%s, %s, %s, %s, %s)"
            val = (timestamp,
                   username,
                   classification_to_int(prediction),
                   file_path,
                   filename)
            try:
                cursor.execute(sql, val)
            except mysql.connector.errors.IntegrityError:
                return 'duplicate name'
            db.commit()

            return {"classification": prediction}
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/<path:username>/weekly_total', methods=['GET'])
def weekly_total(username):
    db = mysql_connect()
    cursor = db.cursor()
    sql = 'SELECT id FROM photos WHERE username=%s AND create_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)'
    cursor.execute(sql, [username])
    cursor.fetchall()
    return_data = {
        "data": cursor.rowcount
    }
    return jsonify(return_data)


@app.route('/<path:username>/monthly_total', methods=['GET'])
def monthly_total(username):
    db = mysql_connect()
    cursor = db.cursor()
    sql = 'SELECT id FROM photos WHERE username=%s AND create_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)'
    cursor.execute(sql, [username])
    cursor.fetchall()
    return_data = {
        "data": cursor.rowcount
    }
    return jsonify(return_data)


@app.route('/<path:username>/last_month_total', methods=['GET'])
def last_month_total(username):
    db = mysql_connect()
    cursor = db.cursor()
    sql = 'SELECT id FROM photos ' \
          'WHERE username=%s ' \
          'AND create_date >= DATE_SUB(NOW(), INTERVAL 60 DAY)' \
          'AND create_date <= DATE_SUB(NOW(), INTERVAL 30 DAY)'
    cursor.execute(sql, [username])
    cursor.fetchall()
    return_data = {
        "data": cursor.rowcount
    }
    return jsonify(return_data)


@app.route('/<path:username>/waste_log_weekly', methods=['GET'])
def waste_log_weekly(username):
    db = mysql_connect()
    cursor = db.cursor()
    sql = 'SELECT create_date, machine_classification FROM photos ' \
          'WHERE username=%s AND create_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)'
    cursor.execute(sql, [username])
    return_list = []
    for item in cursor.fetchall():
        return_data = {
            "date": item[0],
            "type": int_to_classification(item[1])
        }
        return_list.append(return_data)
    e = {
        "list": return_list
    }
    return e


@app.route('/<path:username>/unclassified', methods=["GET"])
def unclassified(username):
    db = mysql_connect()
    cursor = db.cursor()
    sql = "SELECT id, filename, machine_classification FROM photos WHERE username=%(username)s AND user_classification=-1"
    cursor.execute(sql, {'username': username})
    return_list = []
    for item in cursor.fetchall():
        return_data = {
            "id": item[0],
            "filename": item[1],
            "prediction": item[2]
        }
        return_list.append(return_data)
    e = {
        "list": return_list
    }
    return e


# @app.route('/list_unclassified/<path:username>', methods=['GET', 'POST'])
# def list_unclassified(username):
#
#     db = mysql_connect()
#     cursor = db.cursor()
#     sql = "SELECT id, filename FROM photos WHERE username=%(username)s AND user_classification=-1"
#     cursor.execute(sql, {'username': username})
#     paths = cursor.fetchall()
#     # print(paths)
#     return paths


@app.route('/download_by_name/<path:filename>', methods=['GET', 'POST'])
def download_by_path(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/download_by_id/<path:photo_id>', methods=['GET', 'POST'])
def download_by_id(photo_id):
    db = mysql_connect()
    cursor = db.cursor()
    sql = "SELECT path FROM photos WHERE id=%s"
    cursor.execute(sql, [int(photo_id)])
    try:
        path = cursor.fetchone()[0]
    except TypeError:
        path = ""
    if path is None:
        path = ""
    splitpath = path.rsplit('/', 1)
    return send_from_directory(splitpath[0], splitpath[1])


@app.route('/classify/<path:photo_id>/<path:class_int>', methods=['GET', 'POST'])
def classify_image(photo_id, class_int):
    db = mysql_connect()
    cursor = db.cursor()
    classification = int_to_classification(int(class_int))
    if classification == "DELETE":
        return delete_image(photo_id)
    if classification != "Unclassified":
        sql = "UPDATE photos SET user_classification=%s WHERE id=%s AND user_classification=-1"
        val = (class_int, photo_id)
        cursor.execute(sql, val)
        if cursor.rowcount == 1:
            cursor.execute("SELECT filename FROM photos WHERE id=%(photo_id)s", {'photo_id': photo_id})
            filename = cursor.fetchone()[0]
            newpath = BASE_FOLDER + "/" + classification + "/" + filename
            cursor.execute("UPDATE photos SET path='" + newpath + "' WHERE id=%(photo_id)s", {"photo_id": photo_id})
            os.rename(UPLOAD_FOLDER + "/" + filename, newpath)
        db.commit()
        return str(cursor.rowcount)
    return '-1'


@app.route('/delete/<path:photo_id>', methods=['GET', 'POST'])
def delete_image(photo_id):
    db = mysql_connect()
    cursor = db.cursor()
    cursor.execute("SELECT path FROM photos WHERE id=%(photo_id)s AND user_classification=-1", {'photo_id': photo_id})
    path = cursor.fetchone()
    if path is not None:
        os.remove(path[0])
        cursor.execute("DELETE FROM photos WHERE id=%s", [photo_id])
        db.commit()
    return str(cursor.rowcount)


@app.route('/data/<path:username>/<path:class_int>/<path:days>', methods=['GET', 'POST'])
def data(username, class_int, days):
    db = mysql_connect()
    cursor = db.cursor()
    sql = "SELECT * FROM photos WHERE " \
          "username=%s AND " \
          "machine_classification=%s AND " \
          "create_date >= DATE_SUB(NOW(), INTERVAL %s DAY)"
    val = (username, class_int, days)
    cursor.execute(sql, val)
    past_data = cursor.fetchall()
    return past_data


@app.route('/register/<path:username>/<path:password>/<path:email>/<path:household_size>/<path:location>/<path'
           ':device_id>')
def register(username, password, email, household_size, location, device_id):
    db = mysql_connect()
    cursor = db.cursor()
    sql = "SELECT id FROM users WHERE username=%s"
    cursor.execute(sql, [username])
    cursor.fetchall()
    if cursor.rowcount != 0:
        return {"data": 0}
    sql = "SELECT id FROM users WHERE email=%s"
    cursor.execute(sql, [email])
    cursor.fetchall()
    if cursor.rowcount != 0:
        return {"data": 0}
    sql = "SELECT id FROM users WHERE device_id=%s"
    cursor.execute(sql, [device_id])
    cursor.fetchall()
    if cursor.rowcount != 0:
        return {"data": 0}
    sql = "INSERT INTO users (username, password, email, household_size, location, device_id)" \
          "VALUES (%s, %s, %s, %s, %s, %s)"
    val = (username, password, email, household_size, location, device_id)
    cursor.execute(sql, val)
    db.commit()
    return {"data": 1}


@app.route('/login/<path:username>/<path:password>')
def login(username, password):
    db = mysql_connect()
    cursor = db.cursor()
    sql = "SELECT id FROM users WHERE username=%s AND password=%s"
    val = (username, password)
    cursor.execute(sql, val)
    cursor.fetchall()
    if cursor.rowcount == 1:
        return {"data": 1}
    return {"data": 0}
