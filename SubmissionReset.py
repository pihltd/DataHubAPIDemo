# Gets a list of submissions associated witth the account and sends a query to reset the submission timer.
import os
import argparse
import requests
import pandas as pd

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
    
def main(args):

    list_sub_query = """
    query ListSubmissions(
    $status:[String],
    $first: Int,
    $offset: Int,
    $orderBy: String,
    $sortDirection: String){
          listSubmissions(
              status: $status,
              first: $first,
              offset: $offset,
              orderBy: $orderBy,
              sortDirection: $sortDirection){
            total
            submissions{
              _id
              name
              submitterName
              dataCommons
              studyAbbreviation
              dbGaPID
              modelVersion
              status
              conciergeName
              createdAt
              updatedAt
              intention
            }
          }
    }
"""

    list_sub_vars = {"status": ['New', 'In Progress'], "first": -1}
    if args.verbose >= 1:
        print("Getting list of New and In Progress Submissions")
    subres = apiQuery(args.tier.lower(), list_sub_query, list_sub_vars)
    sub_df = pd.DataFrame(subres['data']['listSubmissions']['submissions'])
    if args.verbose >= 2:
        print("Submissions to be updated")
        print(sub_df)
    sublist = sub_df['_id'].unique().tolist()
    
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
    if args.verbose >= 1:
        print("Updating all New and In Progress submissions")
    if args.verbose >= 2:
            reslist = []
    for submissionid in sublist:
        checkvars = {"id": submissionid}
        res = apiQuery(args.tier.lower(), getSubmissionQuery, checkvars)
        if args.verbose >= 2:
            reslist.append(res['data']['getSubmission'])
    if args.verbose >= 2:
        print("Updated submissions")
        res_df = pd.DataFrame(reslist)
        print(res_df)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--tier", required=True,  help="System tier.  'stage" or 'prod')
    parser.add_argument('-v', '--verbose', action='count', default=0, help=("Verbosity: -v main section -vv subroutine messages -vvv data returned shown"))

    args = parser.parse_args()

    main(args)