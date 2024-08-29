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
    

def awsFileUpload(file, signedurl, size):
    #https://docs.aws.amazon.com/AmazonS3/latest/userguide/example_s3_Scenario_PresignedUrl_section.html
    #headers = {'Content-Type': 'text/tab-separated-values', 'Connection':'keep-alive', 'Accept':'*/*', 'Accept-Encoding':'gzip,deflate,br', 'Content-Length':str(size)}
    headers = {'Content-Type': 'text/tab-separated-values', 'Connection':'keep-alive', 'Accept':'*/*', 'Content-Length':str(size)}
    try:
        with open(file, 'rb') as f:
            filetext = f.read()
        res = requests.put(signedurl, data=filetext, headers=headers)
        if res.status_code == 200:
            return res
        else:
            print(f"Error: {res.status_code}")
            return res.content
    except requests.exceptions.HTTPError as e:
        return(f"HTTP error: {e}")
    

#def main():
dev2 = 'https://hub-dev2.datacommons.cancer.gov/api/graphql'
submission_name = 'Jupyter Demo 2'

#Get the submissionID
statusvariables = {"status":"All"}
list_sub_res = apiQuery(dev2, dhq.list_sub_query, statusvariables)

for submission in list_sub_res['data']['listSubmissions']['submissions']:
    if submission['name'] == submission_name:
        submissionid = submission['_id']

print(submissionid)

subtype = "metadata"
metadatafiles = [{"fileName":"/home/pihl/testdata/PDXNet_participant.tsv", "size": 2106 }, {"fileName":"/home/pihl/testdata/PDXNet_sample.tsv", "size":12416}]

#Create the batch
create_batch_variables = {"submissionID": submissionid, "type":subtype, "file":metadatafiles}
create_batch_res = apiQuery(dev2, dhq.create_batch_query, create_batch_variables)
batchid = create_batch_res['data']['createBatch']['_id']

print(batchid)
print (create_batch_res)

'''
#And now try to upload the files
file_upload_result = []
for entry in metadatafiles:
    for metadatafile in create_batch_res['data']['createBatch']['files']:
        if entry['fileName'] == metadatafile['fileName']:
            metares = awsFileUpload(metadatafile['fileName'], metadatafile['signedURL'],entry['size'])
            if metares.status_code == 200:
                succeeded = True
            else:
                succeeded = False
            file_upload_result.append({'fileName':entry['fileName'], 'succeeded': succeeded, 'errors':[], 'skipped':False})

# Update the batch
update_variables = {'batchID':batchid, 'files':file_upload_result}
update_res = apiQuery(dev2, dhq.update_batch_query, update_variables)
print(batchid)
print(update_res)
'''