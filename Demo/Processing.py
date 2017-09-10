from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey
import time
import os
import json

import subprocess
import shlex
from watson_developer_cloud import RetrieveAndRankV1
import pysolr 
# This File Contains the actual code

def start():
    while(1):
        try:
            #check if we run on bluemix
            if 'VCAP_SERVICES' in os.environ:
                vcap_servicesData = json.loads(os.environ['VCAP_SERVICES'])
            else:
                print ("On Local PC")
                json_file = open("static/vcap-local.json")
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
            database_json = client['incoming_warning']
            database_csv = client['incoming_csv']
            
            new_csv = []
            new_json = []
            
            for doc in database_csv:
                new_csv.append(doc[u'data'])
                doc.delete()
            
            for doc in database_json:
                new_json.append(doc[u'data'])
                doc.delete()
            client.disconnect()
            
            #Run Processing 
            if ((len(new_csv)>0) or (len(new_json)>0)):
                print ("Found new data")
                result = main(new_json,new_csv)
                save_data(result)
            else:
                time.sleep(1) 
        except KeyboardInterrupt:
            return 0
    return 0
    # check for new data
    # if we have some call main
    # else sleep for 1 second to avoid issues

def save_data(Results):
    #check if we run on bluemix
    if 'VCAP_SERVICES' in os.environ:
        vcap_servicesData = json.loads(os.environ['VCAP_SERVICES'])
    else:
        print ("On Local PC")
        json_file = open("static/vcap-local.json")
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
    database = client['results']
    database.create_document({"data" : Results, "Time-in": time.time()})
    client.disconnect()
    return 0
    
# Wenting has the actual Python code for here, I am just looking at plotting something 
# and making a Table (plot ids of warnings and table of first 3 collums of stuff
# Format:   List of Json Files....
#           List of CSV Files which are Lists of Lists (each row -> 1 List)
 
def check_status(credentials):
#check the status of the ranker
    RANKER_ID=credentials['ranker_id']
    USERNAME=credentials['username']
    PASSWORD=credentials['password']
    retrieve_and_rank = RetrieveAndRankV1(
        username=USERNAME,
        password=PASSWORD)
        #Running command that checks the status of a ranker
    output = retrieve_and_rank.get_ranker_status(RANKER_ID)
    status=output['status']
    ranker_id=output['ranker_id']
    print (status)
    return status,ranker_id
	
def delete_old_ranker(credentials,ranker_id):
    RANKER_ID=ranker_id
    USERNAME=credentials['username']
    PASSWORD=credentials['password']
    SOLRURL= credentials['url']+"rankers/"
    curl_cmd = 'curl -X DELETE -u "%s":"%s" "%s/{%s}"' %\
    (USERNAME, PASSWORD, SOLRURL, RANKER_ID)
    process = subprocess.Popen(shlex.split(curl_cmd), stdout=subprocess.PIPE)
    output = process.communicate()[0] 
    return output
	
def retrain_ranker(TRAINING_DATA,credentials,ranker_id):
    delete_result=delete_old_ranker(credentials,ranker_id)
    BASEURL=credentials['url']
    SOLRURL= BASEURL+"solr_clusters/"
    RANKER_URL=BASEURL+"rankers"
    USERNAME=credentials['username']
    PASSWORD=credentials['password']
    SOLR_CLUSTER_ID=credentials['cluster_id']
    COLLECTION_NAME=credentials['collection_name']
    #TRAIN_FILE_PATH=''
    GROUND_TRUTH_FILE='static/Historic_Data/cranfield-gt.csv'
    RANKER_NAME="travel_ranker"
    retrieve_and_rank = RetrieveAndRankV1(
        username=USERNAME,
        password=PASSWORD)
#Running command that trains a ranker
    cmd = 'python train.py -u %s:%s -i %s -c %s -x %s -n %s' %\
    (USERNAME, PASSWORD, GROUND_TRUTH_FILE, SOLR_CLUSTER_ID, COLLECTION_NAME,RANKER_NAME )
    try:
        process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
        output = process.communicate()[0]
        output=output.decode("utf-8")
        print (output)        
    except:
        print ('Command:')
        print (cmd)
        print ('Response:')
        print (output)
# creat ranker
    with open(TRAINING_DATA, 'r') as training_data:
        ranker_output = retrieve_and_rank.create_ranker(training_data=training_data, name=RANKER_NAME)
    try:
        print (json.dumps(ranker_output, sort_keys=True, indent=4))
        credentials['ranker_id'] = ranker_output['ranker_id']
    except:
        print ('Command:')
        print (cmd)
        print ('Response:')
        print (ranker_output)
    return credentials 

def main(Json, Csv):
    result = {u"id": [],u"title": [],u"number": [],u"row": []};
    for jfile in Json:
        for doc in jfile:
            result[u"id"].append(doc[u"doc"][u"id"])
            result[u"title"].append(doc[u"doc"][u"title"])
    for csvfile in Csv:
        for doc in csvfile:
            result[u"row"].append(doc[0])
            result[u"number"].append([])
            for i in range(1,len(doc)):
                result[u"number"][-1].append(int(doc[i]))
    credentials = {"cs_ranker_id": "CUSTOM_RANKER_ID", "username": "398941d3-4eec-4044-825d-05ab160a1655", \
               "config_name": "rr_android_config", "cluster_id": "sc2280e5a3_385f_4e4e_940b_8c3e02853b77", \
               "ranker_id": "7ff711x34-rank-2400", "password": "AULMLN26YUSu", "url":\
               "https://gateway.watsonplatform.net/retrieve-and-rank/api/v1/", \
               "collection_name": "rr_andriod_collection1"}
    BASEURL=credentials['url']
    SOLRURL= BASEURL+"solr_clusters/"
    RANKER_URL=BASEURL+"rankers"
    USERNAME=credentials['username']
    PASSWORD=credentials['password']
    SOLR_CLUSTER_ID=credentials['cluster_id']
    COLLECTION_NAME=credentials['collection_name']
    QUESTION="which events exceeding the limites"
    QUESTION = QUESTION.replace(" ","%20")
    RANKER_ID=credentials['ranker_id']
    TRAINING_DATA='static/Historic_Data/trainingdata.csv'
    print (RANKER_ID)
#check the status of ranker  
    credentials=retrain_ranker(TRAINING_DATA,credentials,RANKER_ID)
    status,ranker_id=check_status(credentials)
    if status=='Training':# status=='Available' ||
        print ('Test it!')
        #Running command that queries Solr
        curl_cmd = 'curl -u "%s":"%s" "%s%s/solr/%s/fcselect?ranker_id=%s&q=%s&wt=json&fl=id,title"' %\
       (USERNAME, PASSWORD, SOLRURL, SOLR_CLUSTER_ID, COLLECTION_NAME, credentials['ranker_id'], QUESTION)    
        process = subprocess.Popen(shlex.split(curl_cmd), stdout=subprocess.PIPE)
        output = process.communicate()[0] 
        output=output.decode("utf-8") 
        print (output)
        delete_old_ranker(credentials,credentials['ranker_id'])
    else:
        print ('failed, we will train A new ranker')
        credentials=retrain_ranker(credentials,ranker_id)
        #Running command that queries Solr 
        curl_cmd = 'curl -u "%s":"%s" "%s%s/solr/%s/fcselect?ranker_id=%s&q=%s&wt=json&fl=id,title"' %\
           (USERNAME, PASSWORD, SOLRURL, SOLR_CLUSTER_ID, COLLECTION_NAME, credentials['ranker_id'], QUESTION)    
        process = subprocess.Popen(shlex.split(curl_cmd), stdout=subprocess.PIPE)
        output = process.communicate()[0]
        output=output.decode("utf-8")
        print (output)
        delete_old_ranker(credentials,credentials['ranker_id'])
    return output
	
	
	
