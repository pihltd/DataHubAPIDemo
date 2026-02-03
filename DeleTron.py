# This is the most dangerous script in this collection. DO NOT USE unless you understand what it will do
#
# The purpose of this script is to accept a standard CDRC loading sheet (such as those used to upload data to the Submission Portal)
# and DELETE the information in each row.  
#    ********* If you accidentally delete information, it will have to be resubmitted, there is no undo feature *******
#
# Also note that if a deletion results in orphan nodes, the orphans will also be deleted
#
# YOU HAVE BEEN WARNED


# This script uses a configuration file, please see delete_configs.yml for an example

import argparse
import requests
import pandas as pd
import os
import yaml
import bento_mdf
import sys


deleteQuery = """
    mutation deleteDataRecords(
        $_id: String!, 
        $nodeType: String!, 
        $nodeIds: [String!], 
        $deleteAll: Boolean,
        $exclusiveIDs: [String!]) 
    { deleteDataRecords(
        submissionID: $_id, 
        nodeType: $nodeType,
        nodeIDs: $nodeIds, 
        deleteAll: $deleteAll, 
        exclusiveIDs: $exclusiveIDs)
    { success
      message } } 
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


def getModelInfo(tier, submissionid):
    submissionQuery = """
    query getSubmission($id: ID!){
        getSubmission(_id:$id){
            dataCommons
            modelVersion
        }}
    """
    vars = {'id': submissionid}

    results = apiQuery(tier=tier, query=submissionQuery, variables=vars)
    model = results['data']['getSubmission']['dataCommons']
    modelversion = results['data']['getSubmission']['modelVersion']
    return model, modelversion


def main (args):
    if args.verbose >= 1:
        print("Reading config file")
    configs = readYAML(args.configfile)

    model, modelversion = getModelInfo(configs['tier'], configs['submissionid'])

    if args.verbose >= 1:
        print(f"Getting data model for {model} version {modelversion}")
    temp = []
    for url in configs['mdffiles'][model]:
        temp.append(url.format(modelversion))
    if args.verbose >= 1:
        print("Buidling MDF object")
    mdf = bento_mdf.MDF(*temp)
    if args.verbose >= 2:
        print(f"Built model {mdf.handle} Version {mdf.version}")

    nodekey = mdf.model.nodes[configs['node']].get_key_prop().handle

    if args.verbose >= 2:
        print(f"Node: {configs['node']}\tKey Prop: {nodekey}")

    if args.verbose >=1:
        print(f"Reading delete sheet {configs['deletefile']}")
    delete_df = pd.read_csv(configs['deletefile'], sep="\t")

    if nodekey not in delete_df.columns:
        print(f"Key property {nodekey} not found in load sheet.  Exiting")
        sys.exit(0)
    else:
        deletelist = delete_df[nodekey].unique().tolist()

        deletevars = {"_id": configs['submissionid'], 
                      "nodeType": configs['node'],
                      "nodeIds": deletelist,
                      "deleteAll": False,
                      "exclusiveIds": None
        }
    
        while True:
            a = input(f"{len(deletelist)} entries will be deleted from the {configs['node']} node.  Enter 'yes' to continue or 'no' to abort: ")
            if a == 'yes':
                if args.verbose >= 1:
                    print(f"Removing {len(deletelist)} entries from {configs['node']} ")
                delres = apiQuery(configs['tier'], deleteQuery, deletevars)
                print(f"Deletion Results:\n{delres}")
                break
            elif a == 'no':
                break
            else:
                print("Please enter either 'yes' or 'no'")





if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--configfile", required=True,  help="Configuration file containing all the input info")
    parser.add_argument('-v', '--verbose', action='count', default=0, help=("Verbosity: -v main section -vv subroutine messages -vvv data returned shown"))

    args = parser.parse_args()

    main(args)