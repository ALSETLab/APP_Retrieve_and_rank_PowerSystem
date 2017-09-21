from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey
import os
import re
import json
import time
import csv

# Generate HTML Site to select File of Historical data
def html_LoadHistoric():
    result = "<html><head></head><body>"
    result = result + "<div class='head'> <h2> Select Historic Data File to be streamed </h2> </div>"
    result = result + "<div class='form'> <form action='/startStream'>"
    result = result + "<label for='csv'> Training Set (historic data): </label><select id='csv' name='csv'>"
	
    # Find all csv Files in the directory
    for file in os.listdir(os.getcwd() + "/Historic_Data"):
        if file.endswith(".csv"):
            result = result + "<option>" + file + "</option>"
    
    result = result + "</select><br><br>"
    result = result + "<label for='json'> Warning Data (historic data): </label><select id='json' name='json'>"
    # Find all csv Files in the directory

    for file in os.listdir(os.getcwd() + "/Historic_Data"):
        if file.endswith(".json"):
            result = result + "<option>" + file + "</option>"
    
    result = result + "</select> <br><br>"
    result = result + "<label for='question'> Question for Watson: </label><input id='question' name='question'><br><br>"
    
    
    result = result + "<input type='submit'> </form> </div> </body>"
    
    
    return result

# Put historical Data files into Database
def start_historic( request ):
    regex_result = re.search("startStream\?csv=([a-z,A-Z,0-9,_-]+)\.csv&json=([a-z,A-Z,0-9,_-]+)\.json&question=([a-z,A-Z,0-9,\+_-]+)",request)
    if regex_result is None:
        print("Failed to find specified Files")
        return 0
    else:
        try:
            print("Question: " + regex_result.group(3))
        except:
            print ("Failed to find Question asked")
            return 0
    
    #check if we run on bluemix
    if 'VCAP_SERVICES' in os.environ:
        vcap_servicesData = json.loads(os.environ['VCAP_SERVICES'])
    else:
        print ("On Local PC")
        json_file = open("vcap-local.json")
        s = json_file.read()
        vcap_servicesData = json.loads(s)
        vcap_servicesData = vcap_servicesData[u'services']
    
    # Connect To Cloudant DB
    cloudantNoSQLDBData = vcap_servicesData[u'cloudantNoSQLDB']
    credentials = cloudantNoSQLDBData[0]
    credentialsData = credentials[u'credentials']
    serviceUsername = credentialsData[u'username']
    servicePassword = credentialsData[u'password']
    serviceURL = credentialsData[u'url']
    
    client = Cloudant(serviceUsername, servicePassword, url=serviceURL)
    client.connect()
    database_json = client['incoming_warning'];
   
    
    t = str(int(time.time()))
    #jfile = t + ".json"
    #cfile = t + ".csv"
    json_db = {u"json-file": regex_result.group(2) + ".json", u"csv-file": regex_result.group(1) + ".csv", u"question": regex_result.group(3), u"Time-in" : t}

    newDocument = database_json.create_document(json_db)

    client.disconnect()
    
    return 1

# Retrieve Data from DataBase and return as Json file
def Retrieve_Result ():
    #check if we run on bluemix
    if 'VCAP_SERVICES' in os.environ:
        vcap_servicesData = json.loads(os.environ['VCAP_SERVICES'])
    else:
        print ("On Local PC")
        json_file = open("vcap-local.json")
        s = json_file.read()
        vcap_servicesData = json.loads(s)
        vcap_servicesData = vcap_servicesData[u'services']
    
    # Connect To Cloudant DB
    cloudantNoSQLDBData = vcap_servicesData[u'cloudantNoSQLDB']
    credentials = cloudantNoSQLDBData[0]
    credentialsData = credentials[u'credentials']
    serviceUsername = credentialsData[u'username']
    servicePassword = credentialsData[u'password']
    serviceURL = credentialsData[u'url']
    
    client = Cloudant(serviceUsername, servicePassword, url=serviceURL)
    client.connect()
    database_json = client['results'];
    
    result = {u"data" : [], u"Time" : []}
            
    for dat in database_json:
        result[u"data"].append(dat[u'data'])
        result[u"Time"].append(dat[u'Time-in'])
        
    client.disconnect()    
    return json.dumps(result)
