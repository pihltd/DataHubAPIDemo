import argparse
import requests
import os
import json
import pandas as pd
import numpy as np
import yaml

error_query = """
query retrieveReleasedDataByID(
    $submissionID: String!,
    $nodeType: String!
    $nodeID: String!
){
retrieveReleasedDataByID(
    submissionID: $submissionID,
    nodeType: $nodeType
    nodeID: $nodeID
){
    submissionID
    status
    dataCommons
    dataCommonsDisplayName
    studyID
    nodeType
    nodeID
    props
}
}
"""

submission_nodes_query = """
query getSubmissionNodes(
    $_id: String!,
    $nodeType: String!, 
    $status: String,
    $first: Int, 
    $offset:Int, 
    $orderBy: String, 
    $sortDirection:String
) {
getSubmissionNodes(
    submissionID: $_id
    nodeType: $nodeType
    status: $status
    first: $first
    offset: $offset
    orderBy: $orderBy
    sortDirection: $sortDirection
) {
    total
    IDPropName
    properties
    nodes {
        nodeID
        nodeType
        status
        props
    }
    }
}
"""

getSubmissionQuery = """
        query GetSubmissions(
            $id: ID!    
        ){
            getSubmission(_id:$id){
                _id
                name
                dataCommons
            }
        }

    """

def readYAML(yamlfile):
    with open(yamlfile) as f:
        yamljson = yaml.load(f, Loader=yaml.FullLoader)
    return yamljson



def apiQuery(tier, query, variables):
    if tier == 'prod':
        url = 'https://hub.datacommons.cancer.gov/api/graphql'
        token = os.environ['PRODAPI']
    elif tier == 'stage':
        #Note that use of Stage is for example purposes only, actual submissions should use the production URL.  If you wish to run tests on Stage, please contact the helpdesk.
        url = 'https://hub-stage.datacommons.cancer.gov/api/graphql'
        token = os.environ['STAGEAPI']
    else:
        return('Please provide either "stage" or "prod" as tier values')
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


def diffDataFrame(subid, nodetype, nodeID, tier, query):
    difflist = []
    variables = {'submissionID': subid , 'nodeType': nodetype, 'nodeID': nodeID}
    diffres = apiQuery(tier, query, variables)
    dfcollection = {}
    if 'errors' in diffres:
        return None
    else:
        for entry in diffres['data']['retrieveReleasedDataByID']:
            propstuff = json.loads(entry['props'])
            temp_df = pd.DataFrame(propstuff, index=[entry['submissionID']])
            dfcollection[entry['submissionID']] = temp_df
            keylist = list(dfcollection.keys())
            if len(keylist) >= 2:
                df1 = dfcollection[keylist[0]]
                df2 = dfcollection[keylist[1]]
                diff_df = pd.concat([df1, df2]).drop_duplicates(keep=False)
                difflist.append(diff_df)
        report_df = pd.concat(difflist)
        return report_df

        


def main(args):
    if args.verbose >= 1:
        print(f"Reading config file {args.configfile}")
    configs = readYAML(args.configfile)

    for subid in configs['subid']:
        if args.verbose >= 1:
            print(f"Processing submission ID {subid}")
        for node in configs['nodelist']:
            nodedlist = []
            node_vars = {'_id':subid, 'nodeType':node, 'status':configs['severity'], 'first':-1, 'offset':0, 'orderBy':'studyID', 'sortDirection':'desc'}
            nodedata_res = apiQuery(configs['tier'], submission_nodes_query, node_vars)
            #Set up the dataframe needed to query for errors
            for result in nodedata_res['data']['getSubmissionNodes']['nodes']:
                nodetype = result['nodeType']
                nodeid = result['nodeID']
                report_df = diffDataFrame(subid, nodetype, nodeid, 'stage', error_query)
                if report_df is not None:
                    nodedlist.append(report_df)
                    report_df = pd.concat(nodedlist)
                    report_df.index.name = 'submission_id'
                    report_df['submission_state'] = np.where(report_df.index == subid, 'New', 'Existing')
                    col = report_df.pop('submission_state')
                    report_df.insert(0, 'submission_state', col)
                    report_df.to_csv(f"{configs['outputdirectory']}{subid}_{node}_warning_diffs.csv", sep="\t")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--configfile", required=True,  help="Configuration file containing all the input info")
    parser.add_argument('-v', '--verbose', action='count', default=0, help=("Verbosity: -v main section -vv subroutine messages -vvv data returned shown"))

    args = parser.parse_args()

    main(args)