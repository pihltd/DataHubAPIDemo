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

############################################
#                                          #
#             Components                   #
#                                          #
############################################

dropdown = html.Div([
    html.H2("Submission Update Tool", className="display-4"),
    html.Hr(),
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
            dcc.Store(id="submissionstore")
        ]
    )
])


messages = dcc.Textarea(
        id='messagearea',
        value='Messages Go Here',
        style={'width':'100%', 'height': 300}
    )

updateButton = html.Button('Update Selected', id='updatethis', n_clicks=0)


tableheader = html.Div([
    html.Hr(),
    html.H2("Study Information", id='studytabletitle'),
    html.Hr()
],
    style=CONTENT_STYLE)

submissioncontent = html.Div(
    [
        html.Div(dbc.Spinner(html.Div(id="submissioncontentspinner"), color="primary")),
        html.Div(id="submissioncontent", style=CONTENT_STYLE)
    ]
)

####################################
#                                  #
#         Layouts                  #
#                                  #
####################################

app.layout = html.Div([
    html.Div(
        [dropdown]
    ),
    html.Div([tableheader, submissioncontent]),
    html.Div([updateButton, messages])
])

#app.layout = html.Div(
#    children=[dropdown,
#    tableheader,
#    submissioncontent]
#)


####################################
#                                  #
#         Callbacks                #
#                                  #
####################################

################### Table callbacks #################
@app.callback(
    Output('submissioncontent', 'children'),
    Input('tierselector', 'value')
)

def populateSubmissionsTable(tierselector):
    subjson = getSubmissionData(tierselector)
    sub_df = pd.DataFrame(subjson['data']['listSubmissions']['submissions'])
    sub_df = elapsedTime(sub_df) 
    sub_df.reset_index().to_json(orient='split')

    return dash_table.DataTable(
        data=sub_df.to_dict('records'),
        columns=[{"name": e, "id": e} for e in (sub_df.columns)],
        row_selectable="multi",
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
    [
        Input('updatethis', 'n_clicks'),
        Input('submissioncontent', 'rows'),
        Input('submissioncontent', 'selected_row_indices')
    ]
)

def updateSubmissions(n_clicks,rows, selected_rows_indicies):
    for i in selected_rows_indicies:
        print(f"Row {str(i)} is {rows[i]}")


####################################
#                                  #
#         Run Program              #
#                                  #
####################################


if __name__ == "__main__":
    app.run(port=8050, debug=True)