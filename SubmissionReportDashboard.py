from dash import Dash, html, dcc, dash_table, callback, Output, Input, State
import dash_bootstrap_components  as dbc
import plotly.express as px
import pandas as pd
import requests
import DH_Queries as dhq
import os
from datetime import datetime, timezone



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

def errorPieChart(subid):
    severities = "All"
    first = -1
    offset = 0
    variables = {"id":subid, "severities":severities, "first":first, "offset":offset}
    error_res = apiQuery('STAGE', dhq.qc_check_query, variables)
    error_df = pd.DataFrame(error_res['data']['submissionQCResults']['results'])
    return error_df


def processErrors(error_df):
    #The original error query returns the individual errors as an array, this discombobulates them
    cols = ['submissionid','severity', 'type','title','description']
    flatErrors = pd.DataFrame(columns=cols)
    for index, row in error_df.iterrows():
        id = row['submissionID']
        sev = row['severity']
        type = row['type']
        title = None
        desc = None
        if 'errors' in row:
            errorlist = row['errors']
            for error in errorlist:
                title = error['title']
                desc = error['description']
                flatErrors.loc[len(flatErrors.index)] = [id, sev, type, title, desc]
        if 'warnings' in row:
            warnlist = row['warnings']
            for warn in warnlist:
                title = warn['title']
                desc = warn['description']
                flatErrors.loc[len(flatErrors.index)] = [id, sev, type, title, desc]
        else:
            flatErrors.loc[len(flatErrors.index)] = [id, sev, type, title, desc]
    return flatErrors
            


#Get a list of the studies
studyjson = apiQuery('STAGE', dhq.org_query, None)
columns = ["_id","studyAbbreviation"]
study_df = pd.DataFrame(columns=columns)
for entry in studyjson['data']['getMyUser']['studies']:
    study_df.loc[len(study_df)] = entry
#Get a list of the submissions
subjson = apiQuery('STAGE', dhq.list_sub_query,{"status":["All"]})
sub_df = pd.DataFrame(subjson['data']['listSubmissions']['submissions'])
#print(sub_df)
#Create the elapsedTime column
sub_df = elapsedTime(sub_df)


dhapp = Dash()
dhapp.layout = [

    html.Div([(html.H1(children='Submission Status Dashboard', style={'text-align':'center'})),
            html.Label(['Project Abbreviation:'], style={'font-weight':'bold','text-align':'center'}),
            dcc.Dropdown(study_df.studyAbbreviation,study_df.studyAbbreviation[0], id='study_dropdown'),

            html.H3(children='Project Information (select one project)', style={'text-align':'center'}),
            dash_table.DataTable(id='projectData'),

            html.H3(children='Submissions for the selected Project', style={'text-align':'center'}),
            dash_table.DataTable(id='subData'),
            
            html.H3(children='Elapsed Time', style={'text-align':'center'}),
            dcc.Graph(figure={}, id='elapsedBar'),

            html.H3(children='Validation Severity', style={'text-align':'center'}),
            dcc.Graph(figure = {}, id='severityPie', style={'visibility': 'hidden'}),

            html.H3(children='Error Domains', style={'text-align':'center'}),
            dcc.Graph(figure = {}, id='typePie', style={'visibility':'hidden'}),

            html.H3(children='Error Class', style={'text-align':'center'}),
            dcc.Graph(figure = {}, id='classPie', style={'visibility':'hidden'})
])]



@dhapp.callback(
    [Output('projectData', 'data')],
    [Output('projectData', 'columns')],
    [Output('subData', 'data')],
    [Output('subData','columns')],
    [Output(component_id='elapsedBar', component_property='figure')],
    [Input(component_id='study_dropdown', component_property='value')]
)
def updateProjectTable(study_dropdown):
    selected_df = study_df.loc[study_df['studyAbbreviation']== study_dropdown]
    selectedSub_df = sub_df.loc[sub_df['studyAbbreviation']== study_dropdown]
    elapsedFig = px.bar(selectedSub_df, x='name', y='inactiveDays')

    return(
        selected_df.to_dict('records'),
        [{"name":i, "id":i} for i in (selected_df.columns)],
        selectedSub_df.to_dict('records'),
        [{"name":i, "id":i} for i in (selectedSub_df.columns)],
        elapsedFig
    ) 

@dhapp.callback(
    [Output(component_id="severityPie", component_property="figure")],
    [Output(component_id="severityPie", component_property="style")],
    [Output(component_id="typePie", component_property="figure")],
    [Output(component_id="typePie", component_property="style")],
    [Output(component_id='classPie', component_property='figure')],
    [Output(component_id='classPie', component_property='style')],
    [Input(component_id="subData", component_property='active_cell')],
    [State(component_id='subData', component_property='data')]
)
def errorFigs(active_cell,table_data):
    if active_cell['column'] == 0:
        col = active_cell['column_id']
        row = active_cell['row']
        id = table_data[row][col]
        error_df = errorPieChart(id)
        flaterror_df = processErrors(error_df)
        #print(error_df.severity.value_counts().values, error_df.severity.value_counts().index)
        #print(error_df.head())
        severityfig =px.pie(error_df, values=error_df.severity.value_counts().values, names=error_df.severity.value_counts().index)
        typefig = px.pie(flaterror_df, values=flaterror_df.type.value_counts().values, names=flaterror_df.type.value_counts().index)
        classfig = px.pie(flaterror_df, values=flaterror_df.title.value_counts().values, names=flaterror_df.title.value_counts().index)
        return severityfig, {}, typefig, {}, classfig, {}


if __name__ == '__main__':
    dhapp.run(debug=True)
    #dhapp.run()

