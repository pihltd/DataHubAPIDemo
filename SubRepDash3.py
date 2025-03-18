from dash import Dash, html, dcc, dash_table, callback, Output, Input, State
import dash
import dash_bootstrap_components  as dbc
import plotly.express as px
import pandas as pd
import requests
import DH_Queries as dhq
import os
from datetime import datetime, timezone

# USEFUL Links
#  https://medium.com/@jandegener/writing-a-simple-plotly-dash-app-f5d83b738fd7
#  https://realpython.com/python-dash/
# https://dash-bootstrap-components.opensource.faculty.ai/examples/simple-sidebar/page-2

external_stylesheets = [
    {  "href": "https://fonts.googleapis.com/css2?"
                "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
    dbc.themes.BOOTSTRAP
]

app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True
)
app.title ="DH Dashboard"


#######################################
#                                     #
#       Subroutines                   #
#                                     #
#######################################
def apiQuery(tier, query, variables):    
    if tier == 'DEV2':
        url = 'https://hub-dev2.datacommons.cancer.gov/api/graphql'
        token = os.environ['DEV2API']
    elif tier == 'STAGE':
        url = 'https://hub-stage.datacommons.cancer.gov/api/graphql'
        token = os.environ['STAGEAPI']

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
    
def elapsedTime(submission_df):
    submission_df['createdAt'] = pd.to_datetime(submission_df['createdAt'])
    submission_df['updatedAt'] = pd.to_datetime(submission_df['updatedAt'])
    days = []
    for index, row in submission_df.iterrows():
        update = row['updatedAt']
        now = datetime.now(timezone.utc)
        diff = (now - update).days
        days.append(diff)
    submission_df.insert(8,'inactiveDays',days,True)
    return submission_df

def dropDownList(valuelist):
    finallist = []
    for entry in valuelist:
        finallist.append({'label':entry, 'value':entry})
    return finallist
        

####################################
#                                  #
#         Data calls               #
#                                  #
####################################

#Get a list of the studies
studyjson = apiQuery('STAGE', dhq.org_query, None)
columns = ["_id","studyAbbreviation"]
study_df = pd.DataFrame(columns=columns)
for entry in studyjson['data']['getMyUser']['studies']:
    study_df.loc[len(study_df)] = entry


#Get a list of the submissions
subjson = apiQuery('STAGE', dhq.list_sub_query,{"status":["All"]})
sub_df = pd.DataFrame(subjson['data']['listSubmissions']['submissions'])


#Create the elapsedTime column
sub_df = elapsedTime(sub_df)


############################################
#                                          #
#                 Styles                   #
#                                          #
############################################

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1 rem",
    "background-color": "#f8f9fa"
}

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1 rem"
}

############################################
#                                          #
#             Components                   #
#                                          #
############################################





############################################
#                                          #
#             Layout                       #
#                                          #
############################################

app.layout = html.Div([
    #Layout goes here
],
    style=SIDEBAR_STYLE)

####################################
#                                  #
#         Callbacks                #
#                                  #
####################################



@app.callback(
    Output("studytable", "table"),
    [Input(component_id='studyselector', component_property='value')]
)
def populateTable(studyselector):
    table_df = sub_df.loc[sub_df['studyAbbreviation'] == studyselector]
    id='studytable',
    data=table_df.to_dict('records')
    columns=[{"name":e, "id":e} for e in (table_df.columns)]
    return dash_table.DataTable(data=data, columns=columns)



if __name__ == "__main__":
    app.run_server(port=8050, debug=True)