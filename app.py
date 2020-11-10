import os
from flask_socketio import SocketIO, emit
from flask import Flask, jsonify, request, session,flash
from flask_cors import CORS
from flask import render_template, redirect, url_for, send_from_directory, send_file
from prettytable import PrettyTable
from werkzeug.utils import secure_filename
from time import sleep
import time
import serial
from threading import Thread, Event
import re

import helper


BASEDIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = '/home/pi/csi/flask/templates/images'
app = Flask(__name__, static_folder='/home/pi/csi/flask/templates', static_url_path='/home/pi/csi/flask/templates')
socketio = SocketIO(app, async_mode=None, logger=True, engineio_logger=True)
app.config['DEBUG'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config["SECRET_KEY"] = "OCML3BRawWEUeaxcuKHLpw"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.context_processor
def pre_render():
    data = helper.get_json_by_name("config")
    branding = "Default Brand"
    if data.__contains__("branding"):
        branding = data["branding"]
    return dict(branding=data["branding"])


@app.route("/")
def index():
    hrm_mapped = helper.get_json_by_name('sap_success_factor')
    if not session.get('isAuthenticated') is None:
        if (len(hrm_mapped) <= 0):
            return render_template("dashboard.html", error="HRM Fields Are Not Mapped. Please Mape those to proceed")
        return render_template("dashboard.html")
    else:
        if (len(hrm_mapped) <= 0):
            return render_template("index.html", error="HRM Fields Are Not Mapped. Please Mape those to proceed");
    
        return render_template("index.html")




@app.route("/add-field")
def add_fields():
    fields = helper.get_json_by_name("fields")
    # print (fields)
    return render_template("add-fields.html", fields=fields)



@app.route("/settings", methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        data = helper.get_json_by_name("config")
        return render_template("settings.html", data=data)
    if request.method == 'POST':
        response = request.form.to_dict()
        helper.settings(response)
        return redirect('/settings')


@app.route("/login")
def login():
    if session.get('isAuthenticated') is None:
        return render_template("login.html")
    else:
        return redirect('/')


@app.route("/login", methods=['POST'])
def handle_login():
    data = request.get_json()
    if (data['name'] == "admin" and data['password'] == "password"):
        session["isAuthenticated"] = True
        return jsonify({"message": "Successfully Edited", "status": 200})
    else:
        return jsonify({"message": "Login Failed", "status": 404})

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    if not session.get('isAuthenticated') is None:
        if not os.path.exists('./'+filename):
            return "File Not Found"
        return send_from_directory(directory='./', filename=filename)
    else:
        return "Function Available Only to admin"


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'brand' not in request.files:
            flash('No file part')
            return "No file"
        file = request.files['brand']

        if file.filename == '':
            flash('No selected file')
            return "No File Empty"
        if file and helper.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return "Done"

@app.route("/logout")
def logout():
    session.pop("isAuthenticated", None)
    return redirect('/')


# ----------- Kiosk Mode ----------- #
@app.route('/kiosk1', methods=['GET', 'POST'])
def kiosk1():
    file = helper.get_json_by_name('kiosk_config')
    return render_template('kiosk1.html', brand_name=file['brand_name'], thankyou= file['thankyou_message'], brand_below_message=file['brand_below_message'])

@app.route('/kiosk', methods=['GET', 'POST'])
def kiosk():
    file = helper.get_json_by_name('kiosk_config')
    return render_template('kiosk.html', brand_name=file['brand_name'], thankyou= file['thankyou_message'])


## --------- API ROUTES DEFINED UNDER --------- ##

@app.route('/api/fields', methods=['GET', 'POST'])
def fields():
    if request.method == 'GET':
        fields = helper.get_current_fields()
        response_object = {'status': 'success', "data": fields}
        return jsonify(response_object)
    if request.method == 'POST':
        post_data = request.get_json()
        message = helper.save_fields(post_data)
        return jsonify({"message": message})


@app.route('/api/sap', methods=['GET', 'POST'])
def sap():
    if request.method == 'GET':
        fields = helper.get_current_fields()
        response_object = {'status': 'success', "data": fields}
        return jsonify(response_object)
    if request.method == 'POST':
        post_data = request.get_json()
        print(post_data)
        helper.save_sap_success_factor(post_data)
        return jsonify({"message": "Successfully Edited"})

@app.route('/api/sapconfig', methods=['GET', 'POST'])
def sapconfig():
    if request.method == 'GET':
        feilds = helper.get_json_by_name('sap_config')
        response_object = {'status': 'success', 'data': feilds}
        return jsonify(response_object)
    if request.method == 'POST':
        post_data = request.get_json() 
        if post_data['username'] is None :
            return jsonify({"message": "Username Not Submited", "status": 400})
        if post_data['password'] is None :
            return jsonify({"message": "Password Not Submited", "status": 400})
        if post_data['url'] is None :
            return jsonify({"message": "URL Not Submited", "status": 400})
        message = helper.save_json_by_name('sap_config', post_data)
        return jsonify({"message": message, "status": 200})


@app.route('/api/getJson/<filename>')
def get_json_by_filename(filename):
    fields = helper.get_json_by_name(filename)
    print(fields)
    return jsonify(fields)

@app.route('/api/postJson/<filename>', methods=['POST'])
def save_json_by_filename(filename):
    data = request.get_json()
    response = helper.save_json_by_name(filename, data)
    print(data)
    return jsonify(response)

@app.route('/api/clearSapMappings', methods=['POST'])
def clear_sap_mappings():
    helper.save_sap_success_factor("")
    return jsonify({"message": "Successfully Cleared All Mappings"})


@app.route("/api/renderCSV")
def renderCSV():
    # try:
    a = open("temperature-record.csv", 'r')
    a = a.read().splitlines()
    l1 = a[0]
    l1 = l1.split(',')
    header = []
    for i in range(0, len(l1)):
        header.append(l1[i])
    table = PrettyTable(l1)

    # Adding the data
    for i in range(1, len(a)):
        if(len(a[i])>0):
            table.add_row(a[i].split(','))

    code = table.get_html_string()
    print(code)
    return jsonify({"message": "success", "status": 200, "data": code})
    # except:
    #     return jsonify({"message": "something went wrong", "status": 404, "data": None})



# --------- Instantiating Socket IO --------#

#Temperature Thread
thread = Thread()
thread_stop_event = Event()



def TemperatureFetch():
    deviceOnline = False
    try:
        ser = serial.Serial(
        port='/dev/ttyUSB0',
        baudrate = 9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1
        )
        deviceOnline = True
    except Exception as e:
        print(e)
        deviceOnline=False
        
        
        
    while not thread_stop_event.isSet():
        socketio.emit('deviceOnline', {'device_status': deviceOnline }, namespace='/test')
        x=ser.readline()
        temp_arr = re.findall(r'\d+', str(x))
        print("-------------------->",temp_arr,"\n")
        if len(x) > 0:
            socketio.emit('newnumber', {'number': temp_arr[0]+'.'+temp_arr[1]}, namespace='/test')
            socketio.sleep(1)

@socketio.on('connect', namespace='/test')
def test_connect():
    # need visibility of the global thread object
    global thread
    print('Client connected')

    #Start the random number generator thread only if the thread has not been started before.
    if not thread.isAlive():             
        print("Starting Thread")
        thread = socketio.start_background_task(TemperatureFetch)

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')



# ---------- Instantiating Main ---------#

if __name__ == "__main__":
    
    socketio.run(app)
    #app.run(debug=True, host="127.0.0.1", port=5000)
