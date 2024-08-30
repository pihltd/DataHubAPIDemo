import requests
import os
import DH_Queries as dhq

def apiQuery(url, query, variables):
    token = os.environ['DEV2API']
    headers = {"Authorization": f"Bearer {token}"}
    

    try:
        if variables is None:
            result = requests.post(url = url, headers = headers, json={"query": query})
        else:
            result = requests.post(url = url, headers = headers, json = {"query":query, "variables":variables})
        if result.status_code == 200:
            return result.json()
        else:
            print(f"Error: {result.status_code}")
            return result.content
    except requests.exceptions.HTTPError as e:
        return(f"HTTP Error: {e}")
    
def awsFileUpload2(filedict, signedurl, datadir):
    headers = {'Content-Type': 'text/tab-separated-values'}
    sendthis = []
    for entry in filedict:
        print(f"Working on {entry['fileName']}")
        with open(datadir+entry['fileName'], 'rb') as f:
            filetext = f.read()
            temp = {}
            #sendthis[entry['fileName']] = filetext
            temp['file'] = {entry['fileName']: filetext}
            sendthis.append(temp)

    print(sendthis)
    
    try:
        res = requests.put(signedurl, data=sendthis, headers=headers)
        if res.status_code == 200:
            return res
        else:
            print(f"Error: {res.status_code}")
            return res.content
    except requests.exceptions.HTTPError as e:
        return(f"HTTP Error: {e}")

def awsFileUpload(file, signedurl, size, datadir):
    #https://docs.aws.amazon.com/AmazonS3/latest/userguide/example_s3_Scenario_PresignedUrl_section.html
    #headers = {'Content-Type': 'text/tab-separated-values', 'Connection':'keep-alive', 'Accept':'*/*', 'Accept-Encoding':'gzip,deflate,br', 'Content-Length':str(size)}
    headers = {'Content-Type': 'text/tab-separated-values'}
    try:
        fullFileName = datadir+file
        print(f"Processing {fullFileName}")
        with open(fullFileName, 'rb') as f:
            filetext = f.read()
        res = requests.put(signedurl, data=filetext, headers=headers)
        if res.status_code == 200:
            return res
        else:
            print(f"Error: {res.status_code}")
            return res.content
    except requests.exceptions.HTTPError as e:
        return(f"HTTP error: {e}")
    
def urlComp(batchobject):
    urllist = []
    for entry in batchobject['data']['createBatch']['files']:
        urllist.append(entry['signedURL'])
    for url in urllist:
        for url2 in urllist:
            if url == url2:
                print("URLs match")
            else:
                print("URL Mismatch")
   
    

#def main():
dev2 = 'https://hub-dev2.datacommons.cancer.gov/api/graphql'
submission_name = 'Jupyter Demo 2'
datadir = "/home/pihl/testdata/"

#Get the submissionID
statusvariables = {"status":"All"}
list_sub_res = apiQuery(dev2, dhq.list_sub_query, statusvariables)

for submission in list_sub_res['data']['listSubmissions']['submissions']:
    if submission['name'] == submission_name:
        submissionid = submission['_id']

print(f"SubmissionID: {submissionid}")

subtype = "metadata"
#metadatafiles = [{"fileName":"PDXNet_participant.tsv", "size": 2106 }, {"fileName":"PDXNet_sample.tsv", "size":12416}]
metadatafiles = [{"fileName":"PDXNet_participant.tsv", "size": 2106 }, {"fileName":"PDXNet_sample.tsv", "size":12416},{"fileName":"PDXNet_diagnosis.tsv", "size":6439},{"fileName":"PDXNet_file.tsv", "size":76940},{"fileName":"PDXNet_genomic_info.tsv", "size":283886},{"fileName":"PDXNet_image.tsv", "size":3671},
                      {"fileName":"PDXNet_program.tsv", "size":307},{"fileName":"PDXNet_study.tsv", "size":2171},{"fileName":"PDXNet_treatment.tsv", "size":112}]


#Create the batch
create_batch_variables = {"submissionID": submissionid, "type":subtype, "file":metadatafiles}
create_batch_res = apiQuery(dev2, dhq.create_batch_query, create_batch_variables)
#print(create_batch_res)
batchid = create_batch_res['data']['createBatch']['_id']

#urlComp(create_batch_res)

print(f"BatchID: {batchid}")
#print (create_batch_res)

'''
#Multi file upload
signedurl = create_batch_res['data']['createBatch']['files'][0]['signedURL']
metares = awsFileUpload2(metadatafiles, signedurl, datadir)
file_upload_results = []
if metares.status_code == 200:
    succeed = True
else:
    succeed = False
for entry in metadatafiles:
    file_upload_results.append({'fileName':entry['fileName'], 'succeeded': succeed, 'errors':[], 'skipped':False})
'''



#And now try to upload the files
file_upload_result = []
for entry in metadatafiles:
    for metadatafile in create_batch_res['data']['createBatch']['files']:
        if entry['fileName'] == metadatafile['fileName']:
            print(f"Uploading {metadatafile['fileName']}")
            metares = awsFileUpload(metadatafile['fileName'], metadatafile['signedURL'],entry['size'],datadir)
            if metares.status_code == 200:
                succeeded = True
            else:
                succeeded = False
            file_upload_result.append({'fileName':entry['fileName'], 'succeeded': succeeded, 'errors':[], 'skipped':False})



# Update the batch
print("Sending update")
update_variables = {'batchID':batchid, 'files':file_upload_result}
update_res = apiQuery(dev2, dhq.update_batch_query, update_variables)
print(batchid)
print(update_res)