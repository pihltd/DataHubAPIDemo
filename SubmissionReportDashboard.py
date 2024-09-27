from dash import Dash, html, dcc, dash_table, callback, Output, Input
import plotly.express as px
import pandas as pd
import requests
import DH_Queries as dhq
import os

dev2 = 'https://hub-dev2.datacommons.cancer.gov/api/graphql'

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
    

#Get a list of the studies
studyjson = apiQuery(dev2, dhq.org_query, None)
study_df = pd.DataFrame(studyjson['data']['listApprovedStudiesOfMyOrganization'])
#Get a list of the submissions
subjson = apiQuery(dev2, dhq.list_sub_query,{"status":"All"})
sub_df = pd.DataFrame(subjson['data']['listSubmissions']['submissions'])
print(sub_df)

dhapp = Dash()

dhapp.layout = [
    html.Div(html.H1(children='Submission Status Dashboard', style={'text-align':'center'})),
    html.Div(className='threeColumns', children=[
        html.Label(['Project Abbreviation:'], style={'font-weight':'bold','text-align':'center'}),
        dcc.Dropdown(study_df.studyAbbreviation, id='study_dropdown'),
        html.Label(),
        html.Label()
    ]),
    html.Div(html.H3(children='Project Information', style={'text-align':'center'})),
    html.Div(dash_table.DataTable(id='tblData')),
    html.Div(html.H3(children='Submissions for the selected project', style={'text-align':'center'})),
    html.Div(dash_table.DataTable(id='subData'))
]

@dhapp.callback(
    [Output('tblData', 'data')],
    [Output('tblData', 'columns')],
    [Output('subData', 'data')],
    [Output('subData','columns')],
    [Input('study_dropdown', 'value')]
)
def updateProjectTable(study_dropdown):
    selected_df = study_df.loc[study_df['studyAbbreviation']== study_dropdown]
    selectedSub_df = sub_df.loc[sub_df['studyAbbreviation']== study_dropdown]
    return(selected_df.to_dict('records'),
           [{"name":i, "id":i} for i in (selected_df.columns)],
           selectedSub_df.to_dict('records'),
           [{"name":i, "id":i} for i in (selectedSub_df.columns)])

dhapp.run(debug=True)

