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
    result = result + "<div class='form'> <form action='/web/startStream'>"
    result = result + "<label for='csv'> CSV File (PMU Data): </label><select id='csv' name='csv'>"
	
    # Find all csv Files in the directory
    for file in os.listdir(os.getcwd() + "/Historic_Data"):
        if file.endswith(".csv"):
            result = result + "<option>" + file + "</option>"
    
    result = result + "</select><br><br>"
    result = result + "<label for='json'> JSON File (Warnings): </label><select id='json' name='json'>"
    # Find all csv Files in the directory

    for file in os.listdir(os.getcwd() + "/Historic_Data"):
        if file.endswith(".json"):
            result = result + "<option>" + file + "</option>"
    
    result = result + "</select> <br><br><input type='submit'> </form> </div> </body>"
    return result

# Put historical Data files into Database
def start_historic( request ):
    regex_result = re.search("startStream\?csv=([a-z,A-Z,0-9,_-]+)\.csv&json=([a-z,A-Z,0-9,_-]+)\.json",request)
    if regex_result is None:
        print("Failed to find specified Files")
        return 0
    else:
        try:
            print("JSON File: " + regex_result.group(2))
        except:
            print ("Failed to find CSV file")
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
    database_csv = client['incoming_csv'];
    
    # Write JSON File to Database
    try:
        json_file = open("./Historic_Data/" + regex_result.group(2) + ".json")
        s = re.sub('[\t]', '',json_file.read());
        jsonDocument = json.loads(s)
    except:
       print ("Error Reading JSON File")
       return 0
   
    json_db = {"data": jsonDocument, "Time-in" : time.time()}
    newDocument = database_json.create_document(json_db)

    # Write CSV file to Database
    # Note: NoSQL has a limit on 10 DB writes per second so it won't read anymore

    counter = 0
    rcounter = 0
    csv_data = [];
    with open("./Historic_Data/" + regex_result.group(1) + ".csv", 'rb') as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in csv_reader:
            csv_data.append(row)
        
    newDocument = database_csv.create_document({"data" : csv_data, "Time-in": time.time()})
    
     
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
