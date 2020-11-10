from datetime import datetime
# from mlx90614 import MLX90614
# from smbus2 import SMBus
from time import sleep
import os
import json
import sys
import requests
import shutil
from requests.models import HTTPError
import datetime, time

DEBUG = True

try:
    if sys.argv[1] == 'debug':
        DEBUG = True
except Exception as e:
    pass


TEMPERATURE_READ_INTERVAL = 2000  # ms
TEMPERATURE_REFRESH_RATE = 100  # ms
READ_TIMES = TEMPERATURE_READ_INTERVAL / TEMPERATURE_REFRESH_RATE

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

basePath = './backups'
sourceFile = './temperature-record.csv'
destinationFile = time.strftime("backup_%Y-%m-%d-%H%M%S.csv")

if DEBUG:
    smbus = None
    ir_sensor = None
else:
    smbus = SMBus(1)
    ir_sensor = MLX90614(smbus)


def save(data):
    data['temperature'] = read_temperature()
    write_csv(data)
    return data


def read_temperature():
    fahrenheit = None
    sensor = False
    # return 33
    for i in range(int(TEMPERATURE_READ_INTERVAL/TEMPERATURE_REFRESH_RATE)):
        if ir_sensor:
            fahrenheit = ir_sensor.get_object_1()
            sensor = True
        else:
            fahrenheit = 33
        if i < (int(READ_TIMES)-1):
            sleep(TEMPERATURE_REFRESH_RATE/1000)
        else:
            return fahrenheit



def get_chosen_indices():
    with open('fields.json', 'r') as f:
        all_fields = json.load(f)

    with open("config.json", 'r') as f:
        try:
            chosen = json.load(f)
        except Exception as e:
            chosen = []

    if not chosen or len(chosen) != len(all_fields):
        chosen = [0 for i in all_fields]

    return all_fields, chosen


def get_current_fields():
    with open("fields.json", 'r') as f:
        try:
            chosen = json.load(f)
        except Exception as e:
            chosen = []
    return chosen

def get_json_by_name(name):
    filename= name+".json"
    with open(filename, 'r') as file:
        try:
            jsonData = json.load(file)
        except Exception as e:
            jsonData = []
    return jsonData

def save_json_by_name(name, data):
    filename= name+".json"
    message = "successful"
    with open(filename, 'w') as file:
        try:
            json.dump(data, file)
        except:
            message = "Not Successful"
    return message


def save_fields(data):
    try:
        with open("fields.json", 'w') as f:
            json.dump(data, f)
            backup_csv_records()
    except Exception as e:
        return e
    with open("sap_success_factor.json", "w") as f:
        json.dump("", f)
    return "Save Successfull"

def save_sap_success_factor(data):
    with open("sap_success_factor.json", 'w') as f:
        json.dump(data, f)
        print("done")


# def save_branding(data):
#    with open("branding.txt", "w") as f:
#        f.write(data)


def get_branding():
    with open("branding.txt", "r") as f:
        brand = f.readline()
    return brand

def post_to_HRM(data):
    url = "https://apisalesdemo8.successfactors.com/odata/v2/upsert?$format=json"
    password = "chmS9jXWGs"
    username = "e0007@SFPART053552"
    payload = {"__metadata": {
               "uri": "User('e007')",
               "type": "SFOData.User"
               },
               "userId": "e007",
                }
    with open("sap_success_factor.json", 'r') as f:
        try:
            fields = json.load(f)
        except Exception as e:
            print("error")
        print(fields)
    for key, value in fields.items():
        payload[key] = data[value]
    print(payload)
    try:
        response = requests.post(url, json=payload, auth=(username, password))
        result = response.content.decode("utf8").replace("'", '"')
        data = json.loads(result)
        s = data.get("d")[0]
        if response.status_code == 200:
            print("success")
            return s
        else:
            return "Failed"
    except HTTPError:
        print("Server Error")
        return "Failed"


def write_csv(data):
    with open('fields.json', 'r') as f:
        all_fields = json.load(f)
    headers = [i['name'] for i in all_fields]
    print(headers)
    header_str = 'timestamp,' + ','.join(headers)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data_list = [str(data.get(i) or '').replace(',', " ") for i in headers]
    data_str = timestamp + ',' + ','.join(data_list)
    with open('temperature-record.csv', 'r') as oFile:
         line = oFile.readline().rstrip()
    if line == header_str:
        with open(sourceFile, 'a') as wFile:
            wFile.write(data_str+'\n')
    else:
        didBackup = backup_csv_records()
        if didBackup:
            with open(sourceFile, 'w+') as sFile:
                sFile.write(header_str+'\n')
                sFile.write(data_str+'\n')


def settings(response):
    with open("config.json", 'w') as file:
        json.dump( response, file)

def backup_csv_records():
    if not os.path.isdir(basePath):
        os.mkdir(basePath)
    with open(sourceFile, 'r') as sFile:
        line = sFile.readlines()
        with open("file.csv", 'w+') as dFile:
            try:
                dFile.writelines(line)
            except FileExistsError:
                print("File Exists")
                return False
            except FileNotFoundError:
                print("File Not Found")
                return False
            except Exception as e:
                print(f"Error While Performing Backup : {e}")
                return False
        try:
            os.rename("file.csv", destinationFile)
            dest = shutil.move(destinationFile, './backups')
            print(dest)
        except Exception as e:
            print("Cannot Rename The File {}".format(e))
            return False
        return True

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS