import os
import json
import time
from App import app
from flask import render_template, request, jsonify, make_response
from flask.wrappers import Response
from kubernetes import client, config
import App.configYaml as configYaml
import urllib
import sqlite3

@app.route("/home/", methods=['GET', 'POST'])
def loginPage():
    userId = str(request.args.get('id'))
    if userId != None:
        connection = sqlite3.connect("/app/services/deploy/master.db")
        dbCurr = connection.cursor()
        user = dbCurr.execute('SELECT * FROM userTable WHERE Id='+'"'+userId+'"').fetchall()
        inst = dbCurr.execute('SELECT * FROM instanceTable WHERE userID='+'"'+userId+'"').fetchall()
        print(user)
        if len(user) == 0:
            user = [[]]
            inst = [[]]
        return render_template('index.html',user=user,inst=inst)
    else:
        return render_template('login.html')

@app.route("/", methods=['GET', 'POST'])
def index():
    return render_template('login.html')

@app.route("/loginUser/", methods=['GET', 'POST'])
def loginUser():
    email = request.args.get('email')
    passwd = request.args.get('pass')
    connection = sqlite3.connect("/app/services/deploy/master.db")
    dbCurr = connection.cursor()
    user = dbCurr.execute('SELECT * FROM userTable WHERE email='+'"'+email+'"').fetchall()
    print(user)
    if len(user) != 0:
        return str(user[0][0])
    else:
        print("Failed")
        return "Failed"

@app.route("/registerUser/", methods=['GET', 'POST'])
def registerUser():
    fname = request.args.get('fname')
    lname = request.args.get('lname')
    uname = request.args.get('uname')
    email = request.args.get('email')
    passwd = request.args.get('pass')
    connection = sqlite3.connect("/app/services/deploy/master.db")
    dbCurr = connection.cursor()
    user = dbCurr.execute('SELECT * FROM userTable WHERE email='+'"'+email+'"').fetchall()
    if len(user) == 0:
        dbCurr.execute('INSERT INTO userTable (firstName,lastName,userName,email,password) VALUES ("'+fname+'","'+lname+'","'+uname+'","'+email+'","'+passwd+'")')
        connection.commit()
        return "Success"       
    else:
        return "Failed"

@app.route("/home/cloudVM/", methods=['GET', 'POST'])
def cloudVM():
    connection = sqlite3.connect("/app/services/deploy/master.db")
    dbCurr = connection.cursor()
    userId = request.args.get('id')
    instanceName = request.args.get('name')
    if instanceName != None:
        dbCurr.execute('SELECT userID, instanceName FROM instanceTable WHERE instanceName='+'"'+instanceName+'"')
        data = dbCurr.fetchall()
        return render_template('cloudVM.html', data=data)
    else:
        return "No Pod Service Name Specified"

@app.route("/createCloudVM/", methods=['GET', 'POST'])
def createCloudVM():
    kind = request.args.get('kind')
    name = request.args.get('name')
    image = request.args.get('image')
    mem = request.args.get('mem')
    userID = request.args.get('user')
    status = 'new'
    connection = sqlite3.connect("/app/services/deploy/master.db")
    dbCurr = connection.cursor()
    dbCurr.execute('SELECT * FROM instanceTable WHERE instanceName='+'"'+name+'"')
    cloud = dbCurr.fetchall()
    if len(cloud) == 0:
        configYaml.configs(kind, name, image, mem)
        stream = os.popen('kubectl apply -f /app/services/deploy/kube.yaml')
        output = stream.readlines()
        dbCurr.execute('INSERT INTO instanceTable (userID,instanceName,status) VALUES ('+'"'+userID+'"'+','+'"'+name+'",'+'"'+status+'")')
        connection.commit()
        return "Success"
    else:
        return "Failed"

@app.route("/deleteCloudVM/", methods=['GET', 'POST'])
def deleteCloudVM():
    pod = request.args.get('pod')
    stream = os.popen('kubectl delete pod '+pod+'&')
    output = stream.readlines()
    connection = sqlite3.connect("/app/services/deploy/master.db")
    dbCurr = connection.cursor()
    dbCurr.execute('DELETE FROM instanceTable WHERE instanceName='+'"'+pod+'"')
    connection.commit()
    print(output)
    return "Done"

@app.route("/bashCloudVM/", methods=['GET', 'POST'])
def bashCloudVM():
    pod = request.args.get('pod')
    cmd = request.args.get('cmd')
    stream = os.popen('kubectl exec '+pod+' -- '+ cmd)
    output = stream.readlines()
    print(output)
    return render_template('shell.html', data=output, pod=pod)

@app.route("/systemPage/", methods=['GET', 'POST'])
def systemPage():
    return render_template('system.html')

@app.route("/refreshNgrok/", methods=['GET', 'POST'])
def refreshNgrok():
    pod = request.args.get('pod')
    cmd = 'pkill ngrok'
    stream = os.popen('kubectl exec '+pod+' -- '+ cmd)
    output = stream.readlines()
    print(output)

    cmd_ngrok_80 = './ngrok http 8888&' 
    stream    = os.popen('kubectl exec '+pod+' -- '+ cmd_ngrok_80)
    output = stream.readlines()
    print(output)

    return render_template('cloudVM.html', data=output)

@app.route("/getTunnels/", methods=['GET', 'POST'])
def getTunnels():
    pod = request.args.get('pod')
    cmd = 'curl http://127.0.0.1:4040/api/tunnels'
    stream = os.popen('kubectl exec '+pod+' -- '+ cmd)
    output = stream.readlines()
    data = json.loads(output[0])
    print(data['tunnels'][0])

    return data['tunnels'][0]['public_url']

@app.route("/configureCloudServices/", methods=['GET', 'POST'])
def configureCloudServices():
    pod = request.args.get('pod')
    cmds = [
    'apt install curl -y',
    'apt install unzip -y',
    'apt install python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools -y',
    'apt install python3-pip -y',
    'apt install git -y',
    'pip3 install flask'
    'pip3 install jupyter',
    #'curl -o ngrok.zip https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip',
    #'unzip ngrok.zip',
    #'/ngrok http 8888',
    ]

    for x in cmds:
        stream    = os.popen('kubectl exec '+pod+' -- '+ x)
        output = stream.readlines()
        time.sleep(20)
        print(output)
    return "Done"



@app.route("/configureDebian/", methods=['GET', 'POST'])
def configureDebian():
    pod = request.args.get('pod')
    cmds = [
    'mkdir /var/lib', 
    'mkdir /var/lib/apt', 
    'mkdir /var/lib/dpkg', 
    'touch /var/lib/dpkg/status',
    'mkdir /var/lib/dpkg/updates',
    'mkdir /var/lib/dpkg/info',
    'mkdir /var/lib/dpkg/alternatives',
    'mkdir /var/log;',
    'mkdir /var/log/apt',
    'mkdir /var/cache',
    'mkdir /var/cache/apt',
    'mkdir /var/cache/apt/archives',
    'apt update && apt upgrade -y',
    ]
    for x in cmds:
        stream    = os.popen('kubectl exec '+pod+' -- '+ x)
        output = stream.readlines()
        print(output)
    return "Done"

@app.route("/queryCloudVM/", methods=['GET', 'POST'])
def queryCloudVM():
    pod 	= request.args.get('pod')
    q 		= request.args.get('q')
    commit 	= request.args.get('commit')
    url 	= 'http://127.0.0.1:7777/queryCloudVM/?q='
    cURL 	= url+urllib.parse.quote_plus(q)
    stream    = os.popen('kubectl exec '+pod+' -- curl '+cURL)
    output = stream.readlines()
    return json.dumps(output)










