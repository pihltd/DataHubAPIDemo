from dash import html, dcc, dash_table, Output, Input, State
import dash
import dash_bootstrap_components  as dbc
import requests
import pandas as pd
import io
from datetime import datetime, timezone
from pytz import timezone as tz
import os

#######################################
#                                     #
#       App Definition                #
#                                     #
#######################################

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
    suppress_callback_exceptions=True,
    prevent_initial_callbacks=True,
    update_title="Updating..."
)
app.title ="DH Dashboard"

############################################
#                                          #
#                 Styles                   #
#                                          #
############################################

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "12rem",
    "padding": "2rem 1 rem"
}




#######################################
#                                     #
#       Subroutines                   #
#                                     #
#######################################


def dhAPICreds(tier):
    url = None
    token = None
    if tier == 'production':
        url = 'https://hub.datacommons.cancer.gov/api/graphql'
        token = os.getenv('PRODAPI')
    elif tier == 'stage':
        url = 'https://hub-stage.datacommons.cancer.gov/api/graphql'
        token = os.getenv('STAGEAPI')
    elif tier == 'qa':
        url = 'https://hub-qa.datacommons.cancer.gov/api/graphql'
        token = os.getenv('QAAPI')
    elif tier == 'qa2':
        url = 'https://hub-qa2.datacommons.cancer.gov/api/graphql'
        token = os.getenv('QA2API')
    elif tier == 'dev':
        url = 'https://hub-dev.datacommons.cancer.gov/api/graphql'
        token = os.getenv('DEVAPI')
    elif tier == 'dev2':
        url = 'https://hub-dev2.datacommons.cancer.gov/api/graphql'
        token = os.getenv('DEV2API')
    elif tier == 'localtest':
        url = 'https://this.is.a.test/url/graphql'
        token = os.getenv('LOCALTESTAPI')
    return {'url': url, 'token': token}


def dhApiQuery(url, apitoken, query, variables=None):
    headers = {"Authorization": f"Bearer {apitoken}"}
    try:
        if variables is None:
            result = requests.post(url=url, headers=headers, json={"query": query})
        else:
            result = requests.post(url=url, headers=headers, json={"query": query, "variables": variables})
        if result.status_code == 200:
            return result.json()
        else:
            return (f"Status Code: {result.status_code}\n{result.content}")
    except requests.exceptions.HTTPError as e:
        return (f"HTTPError: {e}")
        

def getSubmissionData(tier):
    tier = tier.lower()
    creds = dhAPICreds(tier)
    list_sub_query = """
            query ListSubmissions($status: [String]!){
            listSubmissions(status: $status){
                submissions{
                _id
                name
                submitterID
                submitterName
                studyAbbreviation
                studyID
                dbGaPID
                createdAt
                updatedAt
                metadataValidationStatus
                fileValidationStatus
                status
                }
            }
        } """
    
    variables = {"status": ["New", "In Progress"]}
    results = dhApiQuery(creds['url'], creds['token'], list_sub_query, variables)
    return results
    


def elapsedTime(submission_df):
    days = []
    for index, row in submission_df.iterrows():
        temp = row['updatedAt'].split('T')
        update = datetime.strptime(temp[0], '%Y-%m-%d')
        update = update.replace(tzinfo=tz('UTC'))
        now = datetime.now(timezone.utc)
        diff = (now - update).days
        days.append(diff)
    submission_df.insert(8,'inactiveDays',days,True)
    return submission_df


def updateSubmissionClock(subid, tier):
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
    vars = {"id": subid}
    creds = dhAPICreds(tier)
    #print(f"Vars: {vars}\n Creds: {creds}\n")
    updatejson = dhApiQuery(creds['url'], creds['token'], getSubmissionQuery, vars)
    #updatejson = {}
    return updatejson




############################################
#                                          #
#             Components                   #
#                                          #
############################################

pageheader = html.Div([
    html.Div(
        html.H1('Submission Update Tool'),
        style={'textAlign':'center'}
    ),
    html.Div(
        children='A tool to reset the submission clock',
        style={'textAlign':'center'}
    )
])

dropdown = html.Div([
    html.Div(
        className='tierdropdown',
        children=[
            dcc.Dropdown(
                id='tierselector',
                options=[
                    {'label': 'Production', 'value': 'production'},
                    {'label': 'Stage', 'value': 'stage'},
                    {'label': 'QA', 'value': 'qa'},
                    {'label': 'QA2', 'value': 'qa2'},
                    {'label': 'Dev', 'value': 'dev'},
                    {'label': 'Dev2', 'value': 'dev2'}
                ],
                placeholder='Select a tier',
                multi=False,
                style={'backgroundcolor':'1E1E1E'},
            ),
        ]
    )
])


errormessages = html.Div(id='printhere', style={'whiteSpace':'pre-line'})

updateButton = html.Button('Reset Time on Selected Submissions', id='updatethis', n_clicks=0)


tableheader = html.Div([
    html.H2("Your current Submissions", style={'textAlign':'center'}),
],
    style=CONTENT_STYLE)

submissioncontent = html.Div(
    [
        html.Div(dbc.Spinner(html.Div(id="submissioncontentspinner"), color="primary")),
        html.Div(id="submissioncontent")
    ]
)

####################################
#                                  #
#         Layouts                  #
#                                  #
####################################

app.layout = html.Div([
    pageheader,
    html.Div([dropdown]),
    html.Hr(),
    html.Div([tableheader]),
    html.Hr(),
    html.Div([submissioncontent]),
    html.Div([updateButton]),
    html.Div([errormessages]),
    dcc.Store(id='substore')
])


####################################
#                                  #
#         Callbacks                #
#                                  #
####################################

################## Datastore callbacks ###############3
@app.callback(
    Output('substore', 'data', allow_duplicate=True),
    Input('tierselector', 'value')
)
def updateSubstore(tierselector):
    subjson = getSubmissionData(tierselector)
    sub_df = pd.DataFrame(subjson['data']['listSubmissions']['submissions'])
    sub_df = elapsedTime(sub_df) 

    return sub_df.reset_index().to_json(orient='split')
################### Table callbacks #################

@app.callback(
        Output('submissioncontent', 'children'),
        Input('substore', 'modified_timestamp'),
        State('substore', 'data')
)
def populateSubmissionsTable2(modified_timestamp, substore):
    sub_df = pd.read_json(io.StringIO(substore), orient='split')
    return dash_table.DataTable(
        id = 'subtable',
        data=sub_df.to_dict('records'),
        columns=[{"name": e, "id": e} for e in (sub_df.columns)],
        row_selectable="multi",
        sort_action='native',
        sort_mode='multi',
        style_table={'overflowX':'auto'},
        style_cell={'overflow':'hidden', 'textOverflow':'ellipsis', 'maxWidth':10, 'textAlign':'center'},
        style_data={'color':'black', 'backgroundColor':'white'},
        style_data_conditional=[{'if':{'row_index':'odd'}, 'backgroundColor': 'rgb(220,220,220)'}],
        style_header={'backgroundColor': 'rgb(210,210,210)', 'color':'black', 'fontWeight':'bold', 'textAlign':'center'},
        tooltip_data=[
            {
                column:{'value': str(value), 'type':'markdown'}
                for column, value in row.items()
            } for row in sub_df.to_dict('records')
        ],
        tooltip_duration=None,
        export_format="csv"
    )
######################## button callback **********************
#
# https://community.plotly.com/t/how-to-get-the-data-of-the-selected-rows-of-dash-table-experiments/8439
#
@app.callback(
    Output('substore', 'data', allow_duplicate=True),
    Input('updatethis', 'n_clicks'),
    State('subtable', 'selected_rows'),
    State('substore', 'data'),
    State('tierselector', 'value')
)

def updateSubmissions(n_clicks,selected_rows, substore, tierselector):
    if n_clicks >= 0:
        sub_df = pd.read_json(io.StringIO(substore), orient='split')
        selected_df = sub_df.iloc[selected_rows]
        collected_res = []
        for index, row in selected_df.iterrows():
            print(row['_id'])
            res = updateSubmissionClock(row['_id'], tierselector)
            collected_res.append({row['name']: res})
        
        subjson = getSubmissionData(tierselector)
        sub_df = pd.DataFrame(subjson['data']['listSubmissions']['submissions'])
        sub_df = elapsedTime(sub_df) 

    return sub_df.reset_index().to_json(orient='split')

####################################
#                                  #
#         Run Program              #
#                                  #
####################################


if __name__ == "__main__":
    app.run(port=8050, debug=True)