import requests
import pandas as pd
import DH_Queries as dhq
import os

def apiQuery(tier, query, variables, queryprint = False):
    if tier == 'DEV2':
        url = 'https://hub-dev2.datacommons.cancer.gov/api/graphql'
        token = os.environ['DEV2API']
    elif tier == 'STAGE':
        url = 'https://hub-stage.datacommons.cancer.gov/api/graphql'
        token = os.environ['STAGEAPI']
    elif tier == 'PROD':
        url = 'https://hub.datacommons.cancer.gov/api/graphql'
        token = os.environ['PRODAPI']
    elif tier == None:
        return("No tier specified")

    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        if variables is None:
            result = requests.post(url = url, headers = headers, json={"query": query})
            if queryprint:
                print(query)
        else:
            result = requests.post(url = url, headers = headers, json = {"query":query, "variables":variables})
            if queryprint:
                print(query)
                print(variables)
        if result.status_code == 200:
            return result.json()
        else:
            print(f"Error: {result.status_code}")
            return result.content
    except requests.exceptions.HTTPError as e:
        return(f"HTTP Error: {e}")

#Get a list of projects and put in df
TIER = 'STAGE'
studyjson = apiQuery(TIER, dhq.org_query, None)
study_df = pd.DataFrame(studyjson['data']['getMyUser']['studies'])
print(study_df.head())

queryterm = '4f1a7385-bda6-4c07-abd0-49e21ec3c1ce'

subjson = apiQuery(TIER, dhq.list_sub_query, {"status":["All"]})
sub_df = pd.DataFrame(subjson['data']['listSubmissions']['submissions'])
print(sub_df.head)

working_df = sub_df.loc[sub_df['studyID'] == queryterm]
print(working_df.head)