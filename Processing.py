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
import csv

from io import StringIO
import requests
import pandas as pd
import numpy as np
from scipy import *
import scipy.linalg as lg
import matplotlib.pyplot as plt	

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
            if ((len(new_csv)>0) and (len(new_json)>0)):
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
    GROUND_TRUTH_FILE='Temp_csv.csv'
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

def func1_get_object_storage_file_with_credentials_9ef91f6a6f554e9fa22e8e2dab2d4852(container, filename):
    """This functions returns a StringIO object containing
    the file content from Bluemix Object Storage."""

    url1 = ''.join(['https://identity.open.softlayer.com', '/v3/auth/tokens'])
    data = {'auth': {'identity': {'methods': ['password'],
            'password': {'user': {'name': 'member_61d8d0026e75d3be7f12e9e3049485ecaf9a8545','domain': {'id': '62cda8210ff64bc0847826085986364d'},
            'password': 'a{VO6~(dbXVRA7j1'}}}}}
    headers1 = {'Content-Type': 'application/json'}
    resp1 = requests.post(url=url1, data=json.dumps(data), headers=headers1)
    resp1_body = resp1.json()
    for e1 in resp1_body['token']['catalog']:
        if(e1['type']=='object-store'):
            for e2 in e1['endpoints']:
                        if(e2['interface']=='public'and e2['region']=='dallas'):
                            url2 = ''.join([e2['url'],'/', container, '/', filename])
    s_subject_token = resp1.headers['x-subject-token']
    headers2 = {'X-Auth-Token': s_subject_token, 'accept': 'application/json'}
    resp2 = requests.get(url=url2, headers=headers2)
    return StringIO(resp2.text)

#import S1 and t
def Static_import_data():
    df_data_1 = pd.read_csv(func1_get_object_storage_file_with_credentials_9ef91f6a6f554e9fa22e8e2dab2d4852('DefaultProjectliw14rpiedu', 'S1.csv'))
    df_data_1.head()
    S1=df_data_1.values 
    df_data_2 = pd.read_csv(func1_get_object_storage_file_with_credentials_9ef91f6a6f554e9fa22e8e2dab2d4852('DefaultProjectliw14rpiedu', 't.csv'))
    df_data_2.head()
    t=df_data_2.values 
    return t,S1

def static_overload(t,S1,p_1,dev0,deltime,simTime):
#Post-fault Over Load Index
#This index is used to observe if the post-fault flows surpass the network capacity, 
#by monitoring the power flows through the transmission lines right after an outage occurs. 
#[Sindex]=static_overload(t,t1,Signal,w,p,d);
# INPUTS
#t - Time vector
#S - Apparent power flow 
# p - Exponent
#d - Deviation allowed of power flow from nominal value, e.g. 10 for +10#    
#OUTPUTS
#Sindex -Overload index
#OVERLOAD 
    pre0=5 
# static_overload.m:23
    post0=100 
# static_overload.m:24
    dev0=dev0 / 100.0
    nl=shape(S1)[1]
    wf_i=ones((1,nl)) 
    Snom=mean(S1[0:pre0,:],0)
    Smax=Snom*(1+dev0) 
    Spost=S1[(S1.shape[0]-post0-1):S1.shape[0],:]
    Smean=mean(Spost,0) 
    # Remove lines out of service
    xxx=[]
    for i in arange(0,nl):
        if abs(Smean[i]) < 1e-2:
            xxx.append(i)
            S1[:,i]=0
            Smean[i]=0
            Snom[i]=0            
    index_red=[]
    indx=[]
    over_line=[]
    rid=[]
    ridh=[]
    i2h=[]
    for i in arange(0,nl):
        indxs_loc=wf_i[0,i]*(abs(Smean[i])/abs(Smax[i]))**p_1
        index_red.append(indxs_loc) 
        if indxs_loc >= 1:
            indx.append(indxs_loc)
            over_line.append(i)
        else:
            indx.append(1)
        rid.append(index_red[i]**(1/float(p_1))) 
        if rid[i]<=1:
            ridh.append(1)
            i2h.append(1)
        else:
            ridh.append(rid[i])
            i2h.append(index_red[i])   
    Fx=[]
    FFx=[]
    for i in arange(0,size(rid)):
        Fx.append(rid[i])
        FFx.append(i)
    F=r_[FFx,Fx]
    F=F.T.copy() 
    fx=[]
    ffx=[]
    for i in arange(0, len(over_line)):
        fx.append(ridh[over_line[i]])
        ffx.append(over_line[i])
    f=r_[ffx,fx]
    f=f.T.copy()
    i2h=np.nan_to_num(i2h)# change the nan to 0    
    Over_S=sum(i2h)/float(nl) 
    
    t1=simTime-3*deltime;
    t2=simTime-2*deltime;
    t3=simTime-deltime;
    t4=simTime;
    S=S1  
    lines=shape(S)
    
    # Sampling three equal intervals towards the end of the simulation for 'k-th' line
    SS1=[];tt1=[];
    SS2=[];tt2=[];
    SS3=[];tt3=[];
    Slope1=[]
    Slope2=[]
    Slope3=[]
    mean_slope=zeros((3,lines[1]))
    slope_change1=zeros((lines[1],2))
    variation=[]
    mm=[]
    for k in arange(0,lines[1]): 
        SS1_each_k=[];tt1_each_k=[]
        SS2_each_k=[];tt2_each_k=[]
        SS3_each_k=[];tt3_each_k=[]
        Slope1_each=[]
        Slope2_each=[]
        Slope3_each=[]
        for i in arange(0,size(t)):
            if t[i,0] > t1 and t[i,0] <=t2: 
                SS1_each_k.append(S[i,k])
                tt1_each_k.append(t[i,0])
            elif t[i,0] > t2 and t[i,0] <=t3:
                SS2_each_k.append(S[i,k])
                tt2_each_k.append(t[i,0])   
            elif  t[i,0] > t3 and t[i,0] <=t4:
                SS3_each_k.append(S[i,k])
                tt3_each_k.append(t[i,0])    
        SS1.append(SS1_each_k)
        tt1.append(tt1_each_k)
        SS2.append(SS2_each_k)
        tt2.append(tt2_each_k)
        SS3.append(SS3_each_k)
        tt3.append(tt3_each_k)
        count1=len(SS1_each_k)
        count2=len(SS2_each_k)
        count3=len(SS3_each_k)
        for i in arange(1,count1):
            Slope1_each.append((SS1_each_k[i]-SS1_each_k[i-1])/(tt1_each_k[i]-tt1_each_k[i-1]))
            if Slope1_each[i-1]==Inf or Slope1_each[i-1]==-Inf:
                Slope1_each.append(0)
        for i in arange(1,count2):
            Slope2_each.append((SS2_each_k[i]-SS2_each_k[i-1])/(tt2_each_k[i]-tt2_each_k[i-1]))
            if Slope2_each[i-1]==Inf or Slope2_each[i-1]==-Inf:
                Slope2_each.append(0) 
        for i in arange(1,count3):
            Slope3_each.append((SS3_each_k[i]-SS3_each_k[i-1])/(tt3_each_k[i]-tt3_each_k[i-1])) 
        Slope1.append(Slope1_each) 
        Slope2.append(Slope2_each) 
        Slope3.append(Slope3_each) 
        # Calculation of mean slope of the interval for 'k-th' line
        mean_slope[0,k]= mean(Slope1_each) 
        mean_slope[1,k]= mean(Slope2_each)
        mean_slope[2,k]= mean(Slope3_each) 
        # Calculation of slope variation between the intervals for 'k-th' line 
        slope_change1[k,0]=mean_slope[1,k]-mean_slope[0,k]
        slope_change1[k,1]=mean_slope[2,k]-mean_slope[1,k]
        # Calculation of the difference between the slope variation for 'k-th' line  
        variation.append(abs(slope_change1[k,1]-slope_change1[k,0]))
    # Assigning all the lines to an array
    for m in arange(0,lines[1]):
        mm.append(m) 
    G=c_[reshape(mm,[lines[1],1]),reshape(variation,[lines[1],1])]
    # loop to find the lines in which the power change/variation is high
    GG=[]
    gg=[]
    for i in arange(0,lines[1]):
        if variation[i]>2.5:
            GG.append(variation[i])
            gg.append(mm[i])
    c1=len(gg)
    if c1>0:
        g=c_[reshape(gg,[c1,1]), reshape(GG,[c1,1])]
    else:
        g=c_[0,0]
    steady_state_lines=[]
    for i in arange(0,lines[1]):
        if slope_change1[i,0]>0 and slope_change1[i, 1]<0 or abs(slope_change1[i,1]) <= abs(slope_change1[i,0]) and variation [i]< 0.01:
            steady_state_lines.append(i)
    Slines=len(steady_state_lines)
    if Slines==0:
        steady_state_lines=0    
    
    return Over_S,i2h,ridh,F,f,G,g,steady_state_lines,slope_change1

def main_static_overload():
    t,S1=Static_import_data()
    # parameters
    p=3
    d=10
    simTime=max(t)
    Faulttime=10
    deltime=10
#determine whether it is overload
    f_x,i2h,ridh,F,f,G,g,steady_state_lines,test  = static_overload(t,S1,p,d,deltime,simTime)
    print ('f_x=',f_x)
    # show the dataset
    plt.figure
    plt.plot(t,S1)
    plt.xlabel('Time (second)')
    plt.ylabel(' Aparent Power')
    plt.show()
    return t,S1,f_x

def func2_get_object_storage_file_with_credentials_9ef91f6a6f554e9fa22e8e2dab2d4852(container, filename):

    url1 = ''.join(['https://identity.open.softlayer.com', '/v3/auth/tokens'])
    data = {'auth': {'identity': {'methods': ['password'], 'password': {'user': {'name': 'member_f206ebb1b5775f6df24fec3b4627ab8ef36d5396','domain': {'id': '62cda8210ff64bc0847826085986364d'},
            'password': 'iDv.U49q0AUirGQ^'}}}}}
    headers1 = {'Content-Type': 'application/json'}
    resp1 = requests.post(url=url1, data=json.dumps(data), headers=headers1)
    resp1_body = resp1.json()
    for e1 in resp1_body['token']['catalog']:
        if(e1['type']=='object-store'):
            for e2 in e1['endpoints']:
                        if(e2['interface']=='public'and e2['region']=='dallas'):
                            url2 = ''.join([e2['url'],'/', container, '/', filename])
    s_subject_token = resp1.headers['x-subject-token']
    headers2 = {'X-Auth-Token': s_subject_token, 'accept': 'application/json'}
    resp2 = requests.get(url=url2, headers=headers2)
    return StringIO(resp2.text)
	
def OLAP_import_data():
    
    PMU_data = pd.read_csv(func2_get_object_storage_file_with_credentials_9ef91f6a6f554e9fa22e8e2dab2d4852('DefaultProjectluigivanfrettigmailcom', 'PMU_dataset.csv'))
    for key in PMU_data.keys():
        PMU_data[key] = PMU_data[key].str.replace('i','j').apply(lambda x: np.complex(x))
        PMU_data[key] = PMU_data[key].abs()
    return PMU_data

def OLAP(PMU_data, p_avg, W):   
    M = PMU_data.values.transpose()
    n1, n2 = M.shape
    M_ob = np.ones((n1, n2), dtype=np.int)
    thrdcoef = 0.01
    M_rec = np.copy(M)
    for i in range(n1):
        for j in range(W, n2):
            if np.random.uniform() <= p_avg:
                M_ob[i,j] = 0
                M_rec[i,j] = 0            
    M_sub = M[:, 0:W]
    U1, S1, V1 = np.linalg.svd(M_sub, full_matrices=True)
    r = 0
    for i in range(len(S1)):
        if S1[i] > thrdcoef*max(S1):
            r += 1
    U_tp1 = U1[:, 0:r]
    
    for i in range(W, n2):
        dim = sum(M_ob[:, i])
        U_tp2 = np.zeros((dim, r))
        M_clm_tp = np.zeros((dim, 1))
        j = 0
        for ii in range(n1):
            if M_ob[ii, i] == 1:
                U_tp2[j, :] = U_tp1[ii, :]
                M_clm_tp[j] = M_rec[ii, i]
                j += 1
        beta_tp = np.matmul(np.linalg.pinv(U_tp2), M_clm_tp)
        V_tp = np.matmul(U_tp1, beta_tp)
        for ii in range(n1):
            if M_ob[ii, i] == 0:
                M_rec[ii, i] = V_tp[ii]
        M_sub = M_rec[:, i-W+1:i+1]
        U2, S2, V2 = np.linalg.svd(M_sub, full_matrices=True)
        r = 0
        for ii in range(len(S2)):
            if S2[ii] > thrdcoef*max(S2):
                r += 1
        U_tp1 = U2[:, 0:r]   
    return M_rec, M_ob*M	
	
def main_MissingData():
    PMU_data = OLAP_import_data() 
    p_avg = 0.1
    W = 30
    M_rec, M_miss = OLAP(PMU_data, p_avg, W)
    n1, n2 = M_rec.shape
    row=3
    #plt.plot(abs(M_miss[row,:]))  
    #plt.plot(abs(M_miss[row+1,:]))  
    #plt.show()
    #plt.plot(abs(M_rec[row,:]))
    #plt.plot(abs(M_rec[row+1,:]))
    #plt.show()
    return abs(M_miss[row,:]),abs(M_rec[row,:])

def func3_get_object_storage_file_with_credentials_9ef91f6a6f554e9fa22e8e2dab2d4852(container, filename):
    """This functions returns a StringIO object containing
    the file content from Bluemix Object Storage."""

    url1 = ''.join(['https://identity.open.softlayer.com', '/v3/auth/tokens'])
    data = {'auth': {'identity': {'methods': ['password'],
            'password': {'user': {'name': 'member_61d8d0026e75d3be7f12e9e3049485ecaf9a8545','domain': {'id': '62cda8210ff64bc0847826085986364d'},
            'password': 'a{VO6~(dbXVRA7j1'}}}}}
    headers1 = {'Content-Type': 'application/json'}
    resp1 = requests.post(url=url1, data=json.dumps(data), headers=headers1)
    resp1_body = resp1.json()
    for e1 in resp1_body['token']['catalog']:
        if(e1['type']=='object-store'):
            for e2 in e1['endpoints']:
                        if(e2['interface']=='public'and e2['region']=='dallas'):
                            url2 = ''.join([e2['url'],'/', container, '/', filename])
    s_subject_token = resp1.headers['x-subject-token']
    headers2 = {'X-Auth-Token': s_subject_token, 'accept': 'application/json'}
    resp2 = requests.get(url=url2, headers=headers2)
    return StringIO(resp2.text)	
	
def angle0(F=None,G=None ): # this function is used to compute subspace angle
    QF=lg.orth(F)
    QG=lg.orth(G) 
    q=min(QF.shape[1],QG.shape[1]) 
    M=np.matmul(QF.T,QG) 
    Ys,s,Zs=np.linalg.svd(M, full_matrices=True)
    a=0  
    for i in arange(0,size(s)).reshape(-1):
        a=a + s[i] ** 2
    a1=sqrt(a / q)
    theta=np.arccos(a1) 
    theta= theta*180 / pi
    theta=abs(theta)
    return theta
	
def Event_import_data():
    #import dictionary 
    df_data_1 = pd.read_csv(func3_get_object_storage_file_with_credentials_9ef91f6a6f554e9fa22e8e2dab2d4852('DefaultProjectliw14rpiedu', 'Offline_Dictionary.csv'))
    df_data_1.head()
    Dictionary=df_data_1.values 
    df_data_2 = pd.read_csv(func3_get_object_storage_file_with_credentials_9ef91f6a6f554e9fa22e8e2dab2d4852('DefaultProjectliw14rpiedu', 'Rank_dic.csv'))
    rank_dic=df_data_2.values 
    #import 12 testing datasets into list Testdata
    df_data_3 = pd.read_csv(func3_get_object_storage_file_with_credentials_9ef91f6a6f554e9fa22e8e2dab2d4852('DefaultProjectliw14rpiedu', 'Generator_Trip13.csv'))
    df_data_4 = pd.read_csv(func3_get_object_storage_file_with_credentials_9ef91f6a6f554e9fa22e8e2dab2d4852('DefaultProjectliw14rpiedu', 'Generator_Trip14.csv'))
    df_data_5 = pd.read_csv(func3_get_object_storage_file_with_credentials_9ef91f6a6f554e9fa22e8e2dab2d4852('DefaultProjectliw14rpiedu', 'Generator_Trip15.csv'))
    df_data_6 = pd.read_csv(func3_get_object_storage_file_with_credentials_9ef91f6a6f554e9fa22e8e2dab2d4852('DefaultProjectliw14rpiedu', 'Three_Phase_Short_Circuit3.csv'))
    df_data_7 = pd.read_csv(func3_get_object_storage_file_with_credentials_9ef91f6a6f554e9fa22e8e2dab2d4852('DefaultProjectliw14rpiedu', 'Three_Phase_Short_Circuit67.csv'))
    df_data_8 = pd.read_csv(func3_get_object_storage_file_with_credentials_9ef91f6a6f554e9fa22e8e2dab2d4852('DefaultProjectliw14rpiedu', 'Three_Phase_Short_Circuit1.csv'))
    df_data_9 = pd.read_csv(func3_get_object_storage_file_with_credentials_9ef91f6a6f554e9fa22e8e2dab2d4852('DefaultProjectliw14rpiedu', 'Load_Change31.csv'))
    df_data_10 = pd.read_csv(func3_get_object_storage_file_with_credentials_9ef91f6a6f554e9fa22e8e2dab2d4852('DefaultProjectliw14rpiedu', 'Load_Change44.csv'))
    df_data_11 = pd.read_csv(func3_get_object_storage_file_with_credentials_9ef91f6a6f554e9fa22e8e2dab2d4852('DefaultProjectliw14rpiedu', 'Load_Change45.csv')) 
    df_data_12 = pd.read_csv(func3_get_object_storage_file_with_credentials_9ef91f6a6f554e9fa22e8e2dab2d4852('DefaultProjectliw14rpiedu', 'Line_Trip3.csv'))
    df_data_13 = pd.read_csv(func3_get_object_storage_file_with_credentials_9ef91f6a6f554e9fa22e8e2dab2d4852('DefaultProjectliw14rpiedu', 'Line_Trip2.csv'))
    df_data_14 = pd.read_csv(func3_get_object_storage_file_with_credentials_9ef91f6a6f554e9fa22e8e2dab2d4852('DefaultProjectliw14rpiedu', 'Line_Trip41.csv'))
    Testdata=[]
    Testdata.append(df_data_3.values);Testdata.append(df_data_4.values);Testdata.append(df_data_5.values)
    Testdata.append(df_data_6.values);Testdata.append(df_data_7.values);Testdata.append(df_data_8.values)
    Testdata.append(df_data_9.values);Testdata.append(df_data_10.values);Testdata.append(df_data_11.values)
    Testdata.append(df_data_12.values);Testdata.append(df_data_13.values);Testdata.append(df_data_14.values)
    return Dictionary, rank_dic, Testdata
	
def Event_Identification(thres=None,gap=None,Testdata=None,event_num=None, Dictionary=None, rank_dic=None): # this function is to identify the type of events
    """ The main idea of this algorithm is to compute the subspaces (represented by dominant part of matrix V ) of each test dataset, compare these subspaces with the Dictionary, and the minimum subspace angle 
    determine the type of the testdata"""
    # initialize
    min_angle=[] 
    type_=[]
    E=[]
    index_min=[]
    voltage=[]
    Vk=[]
    for p in arange(0,event_num).reshape(-1):
        bus_v=Testdata[p] 
        if p < 3:
            t01=51
            t02=151 
            X= (bus_v[0:67,:])  
        elif p < 6:
            t01=71
            t02=171 
            X= (bus_v[0:68,:]) 
        elif p <9 :
            t01=101
            t02=201
            X= (bus_v[0:68,:])         
        elif p < 12:
            t01=51
            t02=151
            X= (bus_v[0:68,:])
        else:
            print ('Please choose from 0 to 11' )
        ## compute subspace
        row,col=X.shape
        voltage.append(X[:,0:400:3])
        for i in arange(0,row).reshape(-1):
            X[i,:]=X[i,:] -  mean(X[i,0:t01])*ones([1,col])
        U, s1, Vh = np.linalg.svd(X[:,t01-1:t02:3]) 
        V = Vh.T  
        sums=0
        ratios=0
        x=0 
        while ratios < thres:
            sums=sums + s1[x]
            ratios=sums / sum(s1) 
            x=x + 1
        dis=[]
        for i in arange(0,x).reshape(-1):
            dis.append(s1[i] / s1[x])
        gap_num=[] 
        for inde,val in enumerate(dis):
            if val > gap:
                gap_num.append(inde)  
        if not gap_num:
            gap_num=1
        k1= max(gap_num)  
        Vk.append(V[:,0:k1])
        E.append(sum(s1[0:k1+1]))
        angles=[] 
        for i in arange(0,49).reshape(-1):
            k12=max(k1,rank_dic[0,i]) 
            theta=angle0(V[:,0:k12],Dictionary[:, 6*i:6*i+k12])  
            angles.append(theta)    
       # identify the type of events by the minimum subspace angle min_angle. The index of the corresponding dictionary atom tells the event type
        min_angle.append(min(angles)) 
        for inde1,val1 in enumerate(angles):
            if np.equal(val1,min_angle[p]):
                index_min.append(inde1)        
        if index_min[p] < 12:
            #for Generator trip and line trip events, energy criterion E and its threshold 0.67 are used to distinguish them further
            if E[p] > 0.67: 
                type_.append('Generator Trip' )
            else:
                type_.append('Line Trip') 
        elif index_min[p] < 19:
                type_.append('Generator Trip') 
        elif index_min[p] < 41:
                type_.append('Three Phase Short Circuit' )
        else:
                type_.append('Load Change')  

    return min_angle,type_,E,voltage,Vk
	
def main_Event_Identification(num):  
    ## parameters
    thres=0.99 
    gap=10
    event_num=12 # The total number of testing samples 
    #import data
    Dictionary, rank_dic, Testdata=Event_import_data()
    # Identify event type by computing subspace angle
    min_angle,type_,E,voltage,Vk= Event_Identification(thres,gap,Testdata,event_num, Dictionary, rank_dic)
    # select the event
    #num=int(input('Please select the number of the event you want to test: \n'))
    #if num > event_num:
        #print ('please select the number less than ' + str(event_num ))
        #num=input('Please select the number of the event you want to test: \n')
        #print ('This is a '+ str(type_[num]) +' event \n' )
        #print ('The minimum subspace angle is '+"{:.2f}".format(min_angle[num])  +' degree \n')
    #else:
        #print ('This is a '+ str(type_[num]) +' event \n') 
        #print ('The minimum subspace angle is '+"{:.2f}".format(min_angle[num])  +' degree \n') 
    #plt.figure
    #plt.plot(voltage[num].T)
    #plt.xlabel('Time  (0.03 second)')
    #plt.ylabel('Voltage (p.u.)') 
    #plt.grid(True)
    #plt.show()
    #plt.figure
    #plt.plot(Vk[num])
    #plt.xlabel('Time (0.03 second)')
    #plt.ylabel('Dominant Singular Vectors') 
    #plt.grid(True)
    #plt.show()
    return str(type_[num]),min_angle[num] 
	
def main(Json, Csv):
    Csv = Csv[0]
    fcsv = open("Temp_csv.csv","wb")
    wr = csv.writer(fcsv, dialect='excel')
    wr.writerows(Csv)
    
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
#check the status of ranker  
    credentials=retrain_ranker(TRAINING_DATA,credentials,RANKER_ID)
    status,ranker_id=check_status(credentials)
    result = {"t": [],"S1": [],"f_x": [],"title":[],u"M_miss":[],u"M_rec":[],,u"Type":[],u"min_angle":[]};
    if status=='Training':# status=='Available' ||
        #Running command that queries Solr
        curl_cmd = 'curl -u "%s":"%s" "%s%s/solr/%s/fcselect?ranker_id=%s&q=%s&wt=json&fl=id,title"' %\
       (USERNAME, PASSWORD, SOLRURL, SOLR_CLUSTER_ID, COLLECTION_NAME, credentials['ranker_id'], QUESTION)    
        process = subprocess.Popen(shlex.split(curl_cmd), stdout=subprocess.PIPE)
        output = process.communicate()[0] 
        output=output.decode() 
        output = json.loads(output)
        delete_old_ranker(credentials,credentials['ranker_id'])
        #num=9    
        #main_Event_Identification(num)
    else:
        print ('failed, we will train A new ranker')
        credentials=retrain_ranker(credentials,ranker_id)
        #Running command that queries Solr 
        curl_cmd = 'curl -u "%s":"%s" "%s%s/solr/%s/fcselect?ranker_id=%s&q=%s&wt=json&fl=id,title"' %\
           (USERNAME, PASSWORD, SOLRURL, SOLR_CLUSTER_ID, COLLECTION_NAME, credentials['ranker_id'], QUESTION)    
        process = subprocess.Popen(shlex.split(curl_cmd), stdout=subprocess.PIPE)
        output = process.communicate()[0]
        output=output.decode()
        output = json.loads(output)
        delete_old_ranker(credentials,credentials['ranker_id'])
    M_miss, M_rec=main_MissingData()
    t,S1,f_x=main_static_overload()
    type_, min_angle=main_Event_Identification(9) # the 9th event
	
    result[u"M_miss"]=list(M_miss)
    result[u"title"].append(u'The PMU measurements with missing data')
    result[u"M_rec"]=list(M_rec)
    result[u"title"].append(u'The PMU measurements after recovery')

    result[u"f_x"]= f_x
    result[u"title"].append(u'The static overload index')
    result[u"S1"] = list(S1[:,0]);
    for i in range(0,len(t)):
        result[u"t"].append(t[i][0]);
    result[u"title"].append(u'The aparent power with time')


    print ('This is a '+ type_ +' event \n')
    print ('The minimum subspace angle is '+"{:.2f}".format(min_angle)  +' degree \n')
    result["Type"]=type_
    result[u"min_anlge"]=min_angle

    plt.plot(result[u"M_miss"])
    plt.show()
    plt.plot(result[u"M_rec"])
    plt.show()
          
    combined_result = {u"Retrieve-Rank": output, u"statid-overload": result};
    return combined_result	
	
	
