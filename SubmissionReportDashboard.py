from dash import html, dcc, dash_table, Output, Input, State
import dash
import dash_bootstrap_components  as dbc
from dash.exceptions import PreventUpdate 
import plotly.express as px
import pandas as pd
import requests
import DH_Queries as dhq
import os
from datetime import datetime, timezone
import json
import io
from pytz import timezone as tz


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
app.title ="Submission Dashboard"



#######################################
#                                     #
#       Subroutines                   #
#                                     #
#######################################
def apiQuery(tier, query, variables, queryprint = False):
    if tier == 'DEV':
        url = 'https://hub-dev.datacommons.cancer.gov/api/graphql'
        token = os.environ['DEVAPI']
    elif tier == 'DEV2':
        url = 'https://hub-dev2.datacommons.cancer.gov/api/graphql'
        token = os.environ['DEV2API']
    elif tier == 'QA':
        url = 'https://hub-qa.datacommons.cancer.gov/api/graphql'
        token = os.environ['QAAPI']
    elif tier == 'QA2':
        url = 'https://hub-qa2.datacommons.cancer.gov/api/graphql'
        token = os.environ['QA2API']
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


def bracketParse(parsethis):
    if ']' in parsethis:
        first = parsethis.split("]")
        errorstring = first[1]
        if "[" in errorstring:
            second = errorstring.split("[")
            return second[0]
        else:
            return errorstring
    else:
        return parsethis


def updateAggregation(df):
    #print(f"\nStarting DF:\n{df}")
    filelist = []
    columns = ['title', 'description', 'count']
    agg_df = pd.DataFrame(columns=columns)
    for index, row in df.iterrows():
        #print(f"\nRow:\n{row}")
        #if row['title'] == 'Updating existing data':
        if 'Updating' in row['title']:
            #if "file_id" in row['description']:
            filelist.append(row['description'])
        else:
            agg_df.loc[len(agg_df)] = row
    #print(f"\nFinal aggregation:\n{agg_df}\n")
    #print(f"File list: {filelist}")
    if len(filelist) > 0:
        agg_df.loc[len(agg_df)] = {'title': 'Updating existing data', 'description': 'File update', 'count': len(filelist)}
    #print(f"\nReturned dataframe:\n{agg_df}")
    return agg_df


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
    updatejson = apiQuery(tier, getSubmissionQuery, vars, False)
    return updatejson


def buildBasicTable(df, diffstyle = None):
    if diffstyle is None:
        styles = [{'if':{'row_index':'odd'}, 'backgroundColor': 'rgb(220,220,220)'}]
    else:
        styles = diffstyle

    print(f"Using styles: {styles}")

    return dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{"name": e, "id": e} for e in (df.columns)],
            style_table={'overflowX':'auto'},
            style_cell={'overflow':'hidden', 'textOverflow':'ellipsis', 'maxWidth':10, 'textAlign':'center'},
            style_data={'color':'black', 'backgroundColor':'white'},
            style_data_conditional=styles,
            style_header={'backgroundColor': 'rgb(210,210,210)', 'color':'black', 'fontWeight':'bold', 'textAlign':'center'},
            tooltip_data=[
                {
                    column:{'value': str(value), 'type':'markdown'}
                    for column, value in row.items()
                } for row in df.to_dict('records')
            ],
            tooltip_duration=None,
            export_format="csv"
        )


def warningStyle(df):
    styles = [{'if':{'row_index':'odd'}, 'backgroundColor': 'rgb(220,220,220)'}]
    for i in range(1, len(df), 2):
        curr_row = df.iloc[i]
        prev_row = df.iloc[i-1]
        for col in df.columns:
            if col != 'EntryType':
                #print(f"Comparing column {col}")
                if curr_row[col] != prev_row[col]:
                    #print(f"Current: {curr_row[col]} DOES NOT match Prev: {prev_row[col]}")
                    styles.append({
                        'if': {'row_index': i, 'column_id': f"{col}"}, 'backgroundColor': '#3498DB', 'color':'black' 
                    })
                #else:
                #    print(f"Current: {curr_row[col]} MATCHES Prev: {prev_row[col]}")
    #print(f"Sending: {styles}")
    #styles = None
    return styles



def diffDataFrame(subid, nodetype, nodeID, tier, query):
    # This is used to create a df for data update warnings
    difflist = []
    variables = {'submissionID': subid , 'nodeType': nodetype, 'nodeID': nodeID}
    diffres = apiQuery(tier, query, variables)
    dfcollection = {}
    if 'errors' in diffres:
        return None
    else:
        for entry in diffres['data']['retrieveReleasedDataByID']:
            tempstuff = json.loads(entry['props'])
            propstuff = {}
            if entry['status'] == "Warning":
                propstuff['EntryType'] = "New"
            else:
                propstuff['EntryType'] = 'Existing'
            for key, value in tempstuff.items():
                propstuff[key] = value
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



def buildUpdateDataframe(subid, tier):
    final_report_df = pd.DataFrame()
    #Get a list of the nodes in the submission
    subvars = {"submissionID": subid}
    sub_summary_res = apiQuery(tier=tier, query=dhq.submission_summary_query, variables=subvars)
    #print(f"Sub Summary Query results:\n{sub_summary_res}\n")
    nodelist = []
    if 'getSubmissionSummary' in sub_summary_res['data']:
        #print("Valid getSubmissionSummary")
        for entry in sub_summary_res['data']['getSubmissionSummary']:
            nodelist.append(entry['nodeType'])
        # Now get the node ID for each of the nodes:
        node_data = {}
        #print(f"Nodelist:\n{nodelist}\n")
        for node in nodelist:
            vars = {"_id":subid, "nodeType":node, "status":"Warning", "first":-1, "offset":0, "orderBy":"nodes", "sortDirection":"Desc"}
            node_res = apiQuery(tier=tier, query=dhq.submission_nodes_query, variables=vars)
            #print(f"Vars: {vars}\nNode results:\n{node_res}\n")
            if 'nodes' in node_res['data']['getSubmissionNodes']:
                for entry in node_res['data']['getSubmissionNodes']['nodes']:
                    node_data[node] = entry['nodeID']
            else:
                return None
            for node, nodeID in node_data.items():
                report_df = diffDataFrame(subid=subid, nodetype=node, nodeID=nodeID, tier=tier, query=dhq.retrieve_released_data_query)
                #print(f"Report dataframe:\n{report_df}\n")
                final_report_df = pd.concat([final_report_df, report_df]).drop_duplicates(keep=False)
        #print(f"Final report df:\n{final_report_df}\n")
        return final_report_df
    else:
        return None

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
    "margin-right": "12rem",
    "padding": "2rem 1 rem"
}

SELECTED_TAB_STYLE = {
    'borderTop': '2px solid #000204',
    'borderBottom': '2px solid #000204',
    'backgroundColor': '#0d7cf5',
    'color': 'white',
    'padding': '6px'
}

TAB_STYLE = {
    'borderBottom': '2px solid #000204',
    'padding': '6px',
    'fontWeight': 'bold'
}

############################################
#                                          #
#             Components                   #
#                                          #
############################################

sidebar = html.Div(
    [
        html.H2("Data Hub", className="display-4"),
        html.Hr(),
        html.Div( 
            className='studydropdown',
            children=[
                #Tier Dropdown
                html.Hr(),
                html.H2("Tiers"),
                html.Hr(),
                html.P(
                    "Select a tier"
                ),
                html.Hr(),
                dcc.Dropdown(
                    id = 'tierselector',
                    options = ['DEV','DEV2','QA','QA2','STAGE', 'PROD'],
                    multi = False,
                    style={'backgroundcolor':'1E1E1E'},
                ),
                dcc.Store(id='studystore'),
                # Study Dropdown
                html.Hr(),
                html.H2("Studies"),
                html.Hr(),
                html.P(
                    'Select a Study'
                ),
                html.Hr(),
                dcc.Dropdown(
                    id='studyselector',
                    options=[],
                    multi=False,
                    style={'backgroundcolor':'1E1E1E'},
                ),
                dcc.Store(id='submissionstore'),
                # Submission Dropdown
                html.Hr(),
                html.H2("Submissions"),
                html.Hr(),
                html.P("Select a submission"),
                html.Hr(),
                dcc.Dropdown(
                    id='subselector',
                    options=[],
                    multi=False,
                    style={'backgroundcolor': '1E1E1E'},
                ),
                # Error Dropdown
                html.Hr(),
                html.H2("Error Details"),
                html.Hr(),
                html.P("Select an error type"),
                html.Hr(),
                dcc.Dropdown(
                    id='errorselector',
                    options = [],
                    multi=False,
                    style={'backgroundcolor': '1E1E1E'},
                ),
                # Warning Dropdown
                html.Hr(),
                html.H2("Warning Details"),
                html.Hr(),
                html.P("Select a warning type"),
                html.Hr(),
                dcc.Dropdown(
                    id = 'warningselector',
                    options = [],
                    multi=False,
                    style={'backgroundcolor': '1E1E1E'}
                ),
                # Data Dropdown
                html.Hr(),
                html.H2('Data Nodes'),
                html.Hr(),
                html.P("Select a data node"),
                html.Hr(),
                dcc.Dropdown(
                    id = 'dataselector',
                    options=[],
                    multi=False,
                    style={'backgroundcolor':'1E1E1E'}
                ),
            ],
            style={'color':'1E1E1E'}
        ),
    ],
    style=SIDEBAR_STYLE,
)



tableheader = html.Div([
    html.Hr(),
    html.H2("Submissions for Study: Select a tier and study from the dropdowns", id='studytabletitle'),
    html.Hr()
    ]
)



errorheader = html.Div(
    [
        html.Hr(),
        html.H2("Error and Warning Details", id='errortitle'),
        html.Hr()
    ]
)



barcharts2 = html.Div([
    dcc.Loading([
        html.Div(
            #Count bar chart
            className='submissionStatusPlot',
            children=[
                html.Hr(),
                html.H2("Submission Status by Count", id='submissionstatusplottitle'),
                dcc.Graph(id='submissionstatusplot')
            ],
            style={'width':'49%', 'display':'inline-block'},
        ),
        html.Div(
            # Percentage bar chart
            className='submissionStatusPlotPercentage',
            children=[
                html.Hr(),
                html.H2("Submission Status by Percentage", id="submissionPercentstatusplottitle"),
                dcc.Graph(id="submissionPercentstatusplot")
            ],
            style={'width':'49%', 'display':'inline-block'},
        ),
    ])
])



errorpie2 = html.Div([
    dcc.Loading([
        html.Div(
            className='ValidationErrorPieChart',
            children=[
                html.Hr(),
                html.H2("Validation Errors", id='validationerrorpietitle'),
                dcc.Graph(id='validationErrorPie')
            ],
            style={'width':'49%', 'display': 'inline-block'},
        ),
        html.Div(
            className="ValidationWarningPieChart",
            children=[
                html.Hr(),
                html.H2("Validation Warnings", id='validationwarningpietitle'),
                dcc.Graph(id='validationWarningPie')
            ],
            style={'width':'49%', 'display':'inline-block'},
        )
    ])
])


errorsummary2 = html.Div([
    dcc.Loading([
        html.Div(
            className='ErrorSummaryTable',
            children=[
                html.Hr(),
                html.H2("Validation Error Summary"),
                html.Div(id="validationerrorsummary")
            ],
            style={'width':'49%', 'display':'inline-block'},
        ),
        html.Div(
            className='WarningSummaryTable',
            children=[
                html.Hr(),
                html.H2("Validation Warning Summary"),
                html.Div(id='validationswarningsummary')
            ],
            style={'width': '49%','display':'inline-block'},
        ),
    ])
])


dataheader = html.Div(
    [
        html.Hr(),
        html.H2("Submitted Data", id='datatitle'),
        html.Hr()
    ]
)

warningheader = html.Div([
    html.Hr(),
    html.H2("Validation Warnings", id='warningtitle'),
    html.Hr()
])

batchheader = html.Div(
    [
        html.Hr(),
        html.H2("Batch History", id="batchtitle"),
        html.Hr()
    ]
)

batchcontent2 = html.Div([
    dcc.Loading([
        html.Div(id="batchcontent")
    ])
])


content = html.Div([
    html.Div(id='page-content'),
    dcc.Store(id='selectedsubmissionstore')
])

updateButton = html.Button('Reset Time on Selected Submissions', id='updatethis', n_clicks=0)

errorcontent2 = html.Div([
    dcc.Loading([
        html.Div(id="errorcontent")
    ])
])

warningcontent = html.Div([
    dcc.Loading([
        html.Div(id='warningcontent')
    ])
])


datacontent2 = html.Div([
    dcc.Loading([
        html.Div(id="datacontent")
    ])
])


# https://stackoverflow.com/questions/70352045/dash-keep-tabs-bar-on-top-and-remember-where-was-scrolled-between-tabs
# The id = tabs-container points to tabs.css in the assets folder and makes the tabs sticky at the top
sitecontent =html.Div([
    dcc.Tabs(
    id='tabs-container', 
    value='tab-status',
    children=[
        dcc.Tab(label="Status",
                value = 'tab-status',
                id = 'statustab',
                style = TAB_STYLE,
                selected_style = SELECTED_TAB_STYLE,
                children=[tableheader, content, updateButton, barcharts2, errorpie2, errorsummary2],
                ),
        dcc.Tab(label="Submission Batch History",
                value="tab-batch",
                id='batchtab',
                style=TAB_STYLE,
                selected_style=SELECTED_TAB_STYLE,
                children=[batchheader, batchcontent2]
                ),
        dcc.Tab(label="Submission Errors",
                value = 'tab-errors',
                id = 'errortab',
                style = TAB_STYLE,
                selected_style = SELECTED_TAB_STYLE,
                children=[errorheader, errorcontent2]
                ),
        dcc.Tab(label='Submission Warnings',
                value = 'warning-data',
                id = 'warningtab',
                style=TAB_STYLE,
                selected_style=SELECTED_TAB_STYLE,
                children=[warningheader, warningcontent]),
        dcc.Tab(label="Submitted Data",
                value='tab-data',
                id='datatab',
                style=TAB_STYLE,
                selected_style=SELECTED_TAB_STYLE,
                children=[dataheader, datacontent2]
                )
        ]
    )
],style=CONTENT_STYLE)


####################################
#                                  #
#         Layouts                  #
#                                  #
####################################

app.layout = html.Div([
    sidebar, sitecontent
])




####################################
#                                  #
#         Callbacks                #
#                                  #
####################################

######## Store callbacks############



@app.callback(
    Output('studystore', 'data'),
    Input(component_id='tierselector', component_property='value'),
)
def populateStudyStore(tierselector):
    studyjson = apiQuery(tierselector, dhq.org_query, None)
    columns = ["_id","studyAbbreviation"]
    study_df = pd.DataFrame(columns=columns)
    for entry in studyjson['data']['getMyUser']['studies']:
        study_df.loc[len(study_df)] = entry
    return study_df.reset_index().to_json(orient='split')


@app.callback(
    Output('submissionstore', 'data', allow_duplicate=True),
    Input(component_id='studystore', component_property='data'),
    State(component_id='studyselector', component_property='value'),
    State(component_id='tierselector', component_property='value'),
)
def populateSubmissionStore(studystore, studyselector, tierselector):
    #Get a list of the submissions
    subjson = apiQuery(tierselector, dhq.list_sub_query, {"status":["All"]})
    sub_df = pd.DataFrame(subjson['data']['listSubmissions']['submissions'])
    #Create the elapsedTime column
    sub_df = elapsedTime(sub_df) 
    return sub_df.reset_index().to_json(orient='split')


@app.callback(
        Output('selectedsubmissionstore', 'data', allow_duplicate=True),
        Input(component_id='studyselector', component_property='value'),
        State(component_id='submissionstore', component_property='data')
)
def populateSelectedSubmissionStore(studyselector, submissionstore):
    sub_df = pd.read_json(io.StringIO(submissionstore),orient='split')
    table_df = sub_df.loc[sub_df['studyAbbreviation'] == studyselector]
    return table_df.reset_index().to_json(orient='split')


######################## Title callbacks ####################################


@app.callback(
    Output("studytabletitle", "children"),
    Input(component_id='studyselector', component_property='value')
)
def changeStudyTableTitle(studyselector):
    if studyselector == None:
        return "Submissions for Study: None"
    else:
        return f"Submissions for Study: {studyselector}"


@app.callback(
    Output("submissionstatusplottitle", "children"),
    Input(component_id='subselector', component_property='value')
)
def changeSubmissionStatusPlotTitle(subselector):
    if subselector == None:
        return "Submission Status by Count"
    else:
        return f"Submission Status by Count: {subselector}"


@app.callback(
    Output("submissionPercentstatusplottitle", "children"),
    Input(component_id='subselector', component_property='value')
)
def changeSubmissionStatusPercentageTitle(subselector):
    if subselector == None:
        return "Submission Status by Percentage"
    else:
        return f"Submission Status by Percentage: {subselector}"


@app.callback(
    Output('validationerrorpietitle', "children"),
    Input(component_id='subselector', component_property='value')
)
def changeValidationErrorPieTitle(subselector):
    if subselector == None:
        return "Validation Errors"
    else:
        return f"Validation Errors: {subselector}"


@app.callback(
    Output('validationwarningpietitle', "children"),
    Input(component_id='subselector', component_property='value')
)
def changeValidationWarningPieTitle(subselector):
    if subselector == None:
        return("Validation Warnings")
    else:
        return f"Validation Warnings: {subselector}"


@app.callback(
    Output("errortitle", "children"),
    Input(component_id="errorselector", component_property='value'),
    State(component_id="studyselector", component_property="value"),
    State(component_id="subselector", component_property="value")
)
def errorTableTitle(errorselector, studyselector, subselector):
    if errorselector == None:
        return("Error Details:")
    else:
        return ("Error Details:",html.Br(),"Study: "+studyselector,html.Br(),"Submission: "+subselector, html.Br(), "Errors: "+errorselector)


@app.callback(
Output("warningtitle", "children"),
Input(component_id='warningselector', component_property='value'),
State(component_id='studyselector', component_property='value'),
State(component_id='subselector', component_property='value')
)
def warningTableTitle(warningselector, studyselector, subselector):
    if warningselector == None:
        return("Warning Details:")
    else:
        return ("Warning Details:",html.Br(),"Study: "+studyselector,html.Br(),"Submission: "+subselector, html.Br(), "Warnings: "+warningselector)


@app.callback(
    Output("datatitle", "children"),
    Input(component_id="dataselector", component_property='value'),
    State(component_id="studyselector", component_property="value"),
    State(component_id="subselector", component_property="value")
)
def dataTableTitle(dataselector, studyselector, subselector):
    if dataselector == None:
        return ("Submitted Data:")
    else:
        return ("Submitted Data:",html.Br(),"Study: "+studyselector,html.Br(),"Submission: "+subselector, html.Br(), "Node: "+dataselector)

@app.callback(
    Output("batchtitle", "children"),
    Input(component_id="subselector", component_property="value")
)
def batchTableTitle(subselector):
    if subselector == None:
        return ("Batch History for Submission")
    else:
        return(f"Batch History for Submission: {subselector}")



####################### Drop-down callbacks##################################
# Tier Selector is pre-populated

# Study Selector
@app.callback(
    Output("studyselector", "options"),
    Input(component_id='studystore', component_property='data')
)
def populateStudyDropdown(studystore):
    study_df = pd.read_json(io.StringIO(studystore), orient='split')
    return study_df['studyAbbreviation'].unique()


# Submissions Selector
@app.callback(
    Output("subselector", "options"),
    Input(component_id='studyselector', component_property='value'),
    State(component_id='submissionstore', component_property='data')
)
def populateSubmissionDropdown(studyselector, submissionstore):
    if studyselector is None:
        raise PreventUpdate
    else:
        sub_df = pd.read_json(io.StringIO(submissionstore),orient='split')
        temp_df=sub_df[sub_df['studyAbbreviation'] == studyselector]
        return temp_df['name'].unique()



# Error Selector
@app.callback(
    Output('errorselector', 'options'),
    Input(component_id='subselector', component_property='value'),
    State(component_id='submissionstore', component_property='data'),
    State(component_id='tierselector', component_property='value'),
)
def populateErrorSelector(subselector, submissionstore, tierselector):
    sub_df = pd.read_json(io.StringIO(submissionstore), orient='split')
    idlist = sub_df.query("name == @subselector")["_id"].tolist()
    if len(idlist)>=1:
        #queryvars = {"submissionID":idlist[0], "severity":"All", "first":-1, "offset":0, "sortDirection": "desc", "orderBy": "displayID"}
        queryvars = {"submissionID":idlist[0], "severity":"Error", "first":-1, "offset":0, "sortDirection": "desc", "orderBy": "displayID"}
        selector_res = apiQuery(tierselector, dhq.summaryQuery, queryvars)
        if selector_res['data']['aggregatedSubmissionQCResults']['total'] == 0:
            return []
        else:
            val_df = pd.DataFrame(selector_res['data']['aggregatedSubmissionQCResults']['results'])
            return val_df['title'].unique()
    else:
        return []
    
#Warning Selector
@app.callback(
        Output('warningselector', 'options'),
        Input(component_id='subselector', component_property='value'),
        State(component_id='submissionstore', component_property='data'),
        State(component_id='tierselector', component_property='value')
)
def populateWarningSelector(subselector, submissionstore, tierselector):
    sub_df = pd.read_json(io.StringIO(submissionstore), orient='split')
    idlist = sub_df.query("name ==@subselector")["_id"].tolist()
    if len(idlist) >= 1:
        queryvars = {"submissionID":idlist[0], "severity":"Warning", "first":-1, "offset":0, "sortDirection": "desc", "orderBy": "displayID"}
        selector_res = apiQuery(tierselector, dhq.summaryQuery, queryvars)
        if selector_res['data']['aggregatedSubmissionQCResults']['total'] == 0:
            return []
        else:
            val_df = pd.DataFrame(selector_res['data']['aggregatedSubmissionQCResults']['results'])
            return val_df['title'].unique()
    else:
        return []


# Data Node selector
@app.callback(
    Output('dataselector', 'options'),
    Input(component_id='subselector', component_property='value'),
    State(component_id='submissionstore', component_property='data'),
    State(component_id='tierselector', component_property='value'),
)
def populateNodeSelector(subselector, submissionstore, tierselector):
    sub_df = pd.read_json(io.StringIO(submissionstore),orient='split')
    idlist = sub_df.query("name == @subselector")["_id"].tolist()
    if len(idlist) >= 1:
        queryvars = {'id':idlist[0]}
        selector_res = apiQuery(tierselector, dhq.submission_stats_query, queryvars)
        temp = []
        for entry in selector_res['data']['submissionStats']['stats']:
            temp.append(entry['nodeName'])
        return temp
    else:
        return []


####################### Table callbacks##########################################

@app.callback(
        Output('submissionstore', 'data', allow_duplicate=True),
        Output('selectedsubmissionstore', 'data', allow_duplicate=True),
        Input(component_id='updatethis', component_property='n_clicks'),
        State(component_id='tierselector', component_property='value'),
        State(component_id='selectedsubmissionstore', component_property='data'),
        State(component_id='selectedstudytable', component_property='selected_rows'),
        State(component_id='submissionstore', component_property='data'),
        State(component_id='studyselector', component_property='value')
)
def updateInactiveTime(n_clicks, tierselector, selectedsubmissionstore, selected_rows, submissionstore, studyselector):
    if n_clicks >= 0:
        sub_df = pd.read_json(io.StringIO(selectedsubmissionstore), orient='split')
        selected_df = sub_df.iloc[selected_rows]
        for index, row in selected_df.iterrows():
            res = updateSubmissionClock(row['_id'], tierselector)
          
        subjson = apiQuery(tierselector, dhq.list_sub_query, {"status":["All"]})
        sub_df = pd.DataFrame(subjson['data']['listSubmissions']['submissions'])
        #Create the elapsedTime column
        sub_df = elapsedTime(sub_df) 
        table_df = sub_df.loc[sub_df['studyAbbreviation'] == studyselector]
        return sub_df.reset_index().to_json(orient='split'), table_df.reset_index().to_json(orient='split')




@app.callback(
        Output("page-content", "children"),
        Input(component_id='selectedsubmissionstore', component_property='modified_timestamp'),
        State(component_id='selectedsubmissionstore', component_property='data')
)
def populateStudyInfoTable(modified_timestamp, selectedsubmissionstore):
    sub_df = pd.read_json(io.StringIO(selectedsubmissionstore),orient='split')
    data=sub_df.to_dict('records')
    #colors = {'new':'#3498DB' , 'error': '#E74C3C', 'warning': '#F4D03F', 'passed': '#16A085'}
    columns=[{"name":e, "id":e} for e in (sub_df.columns)]
    return dash_table.DataTable(id='selectedstudytable',
                                data=data, 
                                columns=columns, 
                                style_table={'overflowX':'auto'},
                                style_cell={'overflow':'hidden', 'textOverflow':'ellipsis', 'maxWidth':10, 'textAlign':'center'},
                                style_data={'color':'black', 'backgroundColor':'white'},
                                style_data_conditional=[{'if':{'row_index':'odd'}, 'backgroundColor': 'rgb(220,220,220)'},
                                                        {'if':{'filter_query':'{inactiveDays} <= 45', 'column_id':'inactiveDays'}, 'backgroundColor':'#16A085', 'color':'black'},
                                                        {'if':{'filter_query':'{inactiveDays} >= 46 && {inactiveDays} <=59', 'column_id':'inactiveDays'}, 'backgroundColor':'#F4D03F', 'color':'black'},
                                                        {'if':{'filter_query':'{inactiveDays} >= 60', 'column_id':'inactiveDays'}, 'backgroundColor':'#E74C3C', 'color':'black'}],
                                style_header={'backgroundColor': 'rgb(210,210,210)', 'color':'black', 'fontWeight':'bold', 'textAlign':'center'},
                                row_selectable="multi",
                                sort_action='native',
                                sort_mode='multi',
                                tooltip_data=[
                                    {
                                        column:{'value': str(value), 'type':'markdown'}
                                        for column, value in row.items()
                                    } for row in sub_df.to_dict('records')
                                ],
                                tooltip_duration=None,
                                export_format="csv"
                                )



@app.callback(
    Output("datacontent", "children"),
    Input(component_id="dataselector", component_property="value"),
    State(component_id='submissionstore', component_property='data'),
    State(component_id='subselector', component_property="value"),
    State(component_id='tierselector', component_property='value'),
)
def populateDataTable(dataselector, submissionstore, subselector, tierselector):
    sub_df = pd.read_json(io.StringIO(submissionstore),orient='split')
    idlist = sub_df.query("name == @subselector")['_id'].tolist()
    if len(idlist) >= 1:
        queryvars = {'_id':idlist[0], 'nodeType':dataselector, 'status':'All', 'first':-1, 'offset':0, 'orderBy':'studyID', 'sortDirection':'desc'}
        data_res = apiQuery(tierselector, dhq.submission_nodes_query, queryvars)
        if 'data' in data_res:
            if data_res['data']['getSubmissionNodes']['total'] == 0:
                return dash_table.DataTable()
            else:
                data_df = pd.DataFrame(columns=data_res['data']['getSubmissionNodes']['properties'])
                for entry in data_res['data']['getSubmissionNodes']['nodes']:
                    data_df.loc[len(data_df)] = json.loads(entry['props'])
                return buildBasicTable(data_df)
        else:
            return dash_table.DataTable()
    else:
        return dash_table.DataTable()



@app.callback(
    Output('errorcontent', 'children'),
    Input(component_id='errorselector', component_property='value'),
    State(component_id='submissionstore', component_property='data'),
    State(component_id='subselector', component_property='value'),
    State(component_id='tierselector', component_property='value'),
)
def errorDetailTable(errorselector, submissionstore, subselector, tierselector):
    sub_df = pd.read_json(io.StringIO(submissionstore),orient='split')
    idlist = sub_df.query("name == @subselector")["_id"].tolist()
    if len(idlist)>=1:
        subvars = {"submissionID":idlist[0], "severity":"Error", "first":-1, "offset":0, "sortDirection": "desc", "orderBy": "displayID"}
        sub_res = apiQuery(tierselector, dhq.summaryQuery, subvars)
        if sub_res['data']['aggregatedSubmissionQCResults']['total'] == 0:
            return dash_table.DataTable()
        else:   
            errorvars = {"id": idlist[0], "severities":"Error", "first": -1, "offset": 0, "orderBy":"displayID", "sortDirection":"desc"}
            detail_res = apiQuery(tierselector, dhq.detailedQCQuery, errorvars)
            columns = ['type', 'title', 'description']
            error_df = pd.DataFrame(columns=columns)
            for result in detail_res['data']['submissionQCResults']['results']:
                for error in result['errors']:
                    #the following filter is needed because if an entity has more then one error, all are returned by the system.  That's a feature, not a bug.
                    if error['title'] == errorselector:
                        error['type'] = 'Error'
                        error_df.loc[len(error_df)] = error
                #Do the same for warnings
                #for warning in result['warnings']:
                #    if warning['title'] == errorselector:
                #        warning['type'] = 'Warning'
                #        error_df.loc[len(error_df)] = warning
                return buildBasicTable(error_df)
    else:
        return dash_table.DataTable()


@app.callback(
        Output('warningcontent', 'children'),
        Input(component_id='warningselector', component_property='value'),
        State(component_id='submissionstore', component_property='data'),
        State(component_id='subselector', component_property='value'),
        State(component_id='tierselector', component_property='value')
)
def warningDetailTable(warningselector, submissionstore, subselector, tierselector):
    sub_df = pd.read_json(io.StringIO(submissionstore), orient='split')
    #print(sub_df)
    idlist = sub_df.query("name == @subselector")["_id"].tolist()
    #print(f"WarningSelector: {warningselector}\nIDList: {idlist}\n")
    if len(idlist) >= 1:
        subvars = {"submissionID":idlist[0], "severity":"Warning", "first":-1, "offset":0, "sortDirection": "desc", "orderBy": "displayID"}
        sub_res = apiQuery(tierselector, dhq.summaryQuery, subvars)
        #print(f"Sub results:\n{sub_res}\n")
        if sub_res['data']['aggregatedSubmissionQCResults']['total'] == 0:
            return dash_table.DataTable()
        else:
            errorvars = {"id": idlist[0], "severities":"Warning", "first": -1, "offset": 0, "orderBy":"displayID", "sortDirection":"desc"}
            detail_res = apiQuery(tierselector, dhq.detailedQCQuery, errorvars)
            #print(f"Detailed results:\n{detail_res}\n")
            # TODO: for replacement warnings need to build in special handling
            if warningselector == 'Updating existing data':
                #print("calling buildUpdateDataFrame")
                update_df = buildUpdateDataframe(subid=idlist[0], tier=tierselector)
                #print(f"Updating DF: \n{update_df}\n")
                if update_df is not None:
                    styles = warningStyle(update_df)
                    print(f"Sending style: {styles}")
                    return buildBasicTable(update_df, styles)
                else:
                    return dash_table.DataTable()
            else:
                columns = ['type', 'title', 'description']
                warning_df = pd.DataFrame(columns=columns)
                #print(f"Other warnings:\n{warning_df}\n")
                for result in detail_res['data']['submissionQCResults']['results']:
                    for warning in result['warnings']:
                        if warning['title'] == warningselector:
                            warning['type'] = 'Warning'
                            warning_df.loc[len(warning_df)] = warning
                        return buildBasicTable(warning_df)
    else:
        return dash_table.DataTable()
        


@app.callback(
    Output("batchcontent", "children"),
    Input(component_id="subselector", component_property="value"),
    State(component_id='submissionstore', component_property='data'),
    State(component_id='tierselector', component_property='value')
)
def populateBatchTable(subselector, submissionstore, tierselector):
    submission_df = pd.read_json(io.StringIO(submissionstore), orient='split')
    idlist = submission_df.query("name == @subselector")["_id"].tolist()
    if len(idlist)>=1:
        queryvars = {"submissionID":idlist[0], "orderBy":"createdAt", "sortDirection":"DESC"}
        batch_res = apiQuery(tierselector, dhq.list_batch_query, queryvars)
        if batch_res['data']['listBatches']['total'] == 0:
            return dash_table.DataTable()
        else:
            batch_df = pd.DataFrame(columns=list(batch_res['data']['listBatches']['batches'][0].keys()))
            for batch in batch_res['data']['listBatches']['batches']:
                batch_df.loc[len(batch_df)] = batch
            #Need to covert errors and files to string otherwise it borks the table
            batch_df['errors'] = batch_df['errors'].astype(str)
            batch_df['files'] = batch_df['files'].astype(str)
            return buildBasicTable(batch_df)
    else:
        return dash_table.DataTable()


@app.callback(
    Output("validationerrorsummary", "children"),
    Input(component_id='subselector', component_property='value'),
    State(component_id='submissionstore', component_property='data'),
    State(component_id='tierselector', component_property='value'),
)
def validationErrorSummaryTable(subselector, submissionstore, tierselector):
    sub_df = pd.read_json(io.StringIO(submissionstore),orient='split')
    idlist = sub_df.query("name == @subselector")["_id"].tolist()
    if len(idlist) >= 1:
        subvars = {"submissionID":idlist[0], "severity":"Error", "first":-1, "offset":0, "sortDirection": "desc", "orderBy": "displayID"}
        sub_res = apiQuery(tierselector, dhq.summaryQuery, subvars)
        if sub_res['data']['aggregatedSubmissionQCResults']['total'] == 0:
            return dash_table.DataTable()
        else:
            columns = ['type', 'title', 'description']
            error_df = pd.DataFrame(columns=columns)
            errorvars = {"id": idlist[0], "severities":"Error", "first": -1, "offset": 0, "orderBy":"displayID", "sortDirection":"desc"}
            detail_res = apiQuery(tierselector, dhq.detailedQCQuery, errorvars)
            for result in detail_res['data']['submissionQCResults']['results']:
                for error in result['errors']:
                    message = bracketParse(error['description'])
                    error_df.loc[len(error_df)] = {'type':'Error', 'title':error['title'], 'description':message}
            summary_df = error_df.groupby(['title', 'description']).size().reset_index().rename(columns={0:'count'}).sort_values(by='count', ascending=False)
            return buildBasicTable(summary_df)
    else:
        return dash_table.DataTable()



@app.callback(
    Output("validationswarningsummary", "children"),
    Input(component_id='subselector', component_property='value'),
    State(component_id='submissionstore', component_property='data'),
    State(component_id='tierselector', component_property='value'),
)
def validationWarningSummaryTable(subselector, submissionstore, tierselector):
    sub_df = pd.read_json(io.StringIO(submissionstore),orient='split')
    idlist = sub_df.query("name == @subselector")["_id"].tolist()
    if len(idlist) >= 1:
        subvars = {"submissionID":idlist[0], "severity":"Warning", "first":-1, "offset":0, "sortDirection": "desc", "orderBy": "displayID"}
        sub_res = apiQuery(tierselector, dhq.summaryQuery, subvars)
        #print(f"Warning query results:\n{sub_res}")
        if sub_res['data']['aggregatedSubmissionQCResults']['total'] == 0:
            return dash_table.DataTable()
        else:
            columns = ['type', 'title', 'description']
            error_df = pd.DataFrame(columns=columns)
            errorvars = {"id": idlist[0], "severities":"Warning", "first": -1, "offset": 0, "orderBy":"displayID", "sortDirection":"desc"}
            detail_res = apiQuery(tierselector, dhq.detailedQCQuery, errorvars)
            #print(f"Warnign detail:\n{detail_res}")
            for result in detail_res['data']['submissionQCResults']['results']:
                for error in result['warnings']:
                    message = bracketParse(error['description'])
                    error_df.loc[len(error_df)] = {'type':'Error', 'title':error['title'], 'description':message}
                #print(f"Error dataframe:\n{error_df}")
            temp_df = error_df.groupby(['title', 'description']).size().reset_index().rename(columns={0:'count'}).sort_values(by='count', ascending=False)
            #print(f"Temp dataframe:\n{temp_df}")
            summary_df = updateAggregation(temp_df)
            summary_df = summary_df.sort_values(by='count', ascending=False)
            #print(f"Summary dataframe:\n{summary_df}")
            return buildBasicTable(summary_df)
    else:
        return dash_table.DataTable()
            
############################## Graph Callbacks###################################



@app.callback(
    Output('validationErrorPie', 'figure'),
    Input(component_id='subselector', component_property='value'),
    State(component_id='submissionstore', component_property='data'),
    State(component_id='tierselector', component_property='value'),
)
def validationErrorPieChart(subselector, submissionstore, tierselector):
    sub_df = pd.read_json(io.StringIO(submissionstore),orient='split')
    idlist = sub_df.query("name == @subselector")["_id"].tolist()
    #colors = {'new':'blue', 'error': 'red', 'warning':'yellow', 'passed':'green'}
    if len(idlist)>=1:
        valvars = {"submissionID":idlist[0], "severity":"Error", "first":-1, "offset":0, "sortDirection": "desc", "orderBy": "displayID"}
        val_res = apiQuery(tierselector, dhq.summaryQuery, valvars)
        if val_res['data']['aggregatedSubmissionQCResults']['total'] == 0:
            return  px.pie()
        else:
            val_df = pd.DataFrame(val_res['data']['aggregatedSubmissionQCResults']['results'])
            return px.pie(val_df, values='count', names='title', hole=.3)
    else:
        return px.pie()



@app.callback(
    Output('validationWarningPie', 'figure'),
    Input(component_id='subselector', component_property='value'),
    State(component_id='submissionstore', component_property='data'),
    State(component_id='tierselector', component_property='value'),
)
def validationWarningPieChart(subselector, submissionstore, tierselector):
    sub_df = pd.read_json(io.StringIO(submissionstore),orient='split')
    idlist = sub_df.query("name == @subselector")["_id"].tolist()
    #colors = {'new':'blue', 'error': 'red', 'warning':'yellow', 'passed':'green'}
    if len(idlist)>=1:
        valvars = {"submissionID":idlist[0], "severity":"Warning", "first":-1, "offset":0, "sortDirection": "desc", "orderBy": "displayID"}
        val_res = apiQuery(tierselector, dhq.summaryQuery, valvars)
        if val_res['data']['aggregatedSubmissionQCResults']['total'] == 0:
            return  px.pie()
        else:
            val_df = pd.DataFrame(val_res['data']['aggregatedSubmissionQCResults']['results'])
            return px.pie(val_df, values='count', names='title', hole=.3)
    else:
        return px.pie()



@app.callback(
    Output('submissionstatusplot', 'figure'),
    Input(component_id="subselector", component_property="value"),
    State(component_id='submissionstore', component_property='data'),
    State(component_id='tierselector', component_property='value'),
)
def subStatusChart(subselector, submissionstore, tierselector):
    sub_df = pd.read_json(io.StringIO(submissionstore),orient='split')
    idlist = sub_df.query("name == @subselector")["_id"].tolist()
    #colors = {'new':'blue', 'error': 'red', 'warning':'yellow', 'passed':'green'}
    #colors = {'new':'#74D4FF' , 'error': '#FFA2A2', 'warning': '#FFF085', 'passed': '#7BF1A8'}
    colors = {'new':'#3498DB' , 'error': '#E74C3C', 'warning': '#F4D03F', 'passed': '#16A085'}
    if len(idlist) >= 1:
        qvars = {'id': idlist[0]}
        query_res = apiQuery(tierselector, dhq.submission_stats_query, qvars)
        columns = ['nodeName', 'total', 'new', 'error', 'warning', 'passed']
        substats_df = pd.DataFrame(columns=columns)
        for entry in query_res['data']['submissionStats']['stats']:
            substats_df.loc[len(substats_df)] = entry
        return px.bar(substats_df, x='nodeName', y=['new', 'error', 'warning', 'passed'], color_discrete_map=colors)
    else:
        return px.bar()



@app.callback(
    Output("submissionPercentstatusplot", "figure"),
    Input(component_id="subselector", component_property="value"),
    State(component_id="submissionstore", component_property="data"),
    State(component_id="tierselector", component_property="value")
)
def subStatusPercentageChart(subselector, submissionstore, tierselector):
    sub_df = pd.read_json(io.StringIO(submissionstore),orient='split')
    idlist = sub_df.query("name == @subselector")["_id"].tolist()
    #colors = {'new':'blue', 'error': 'red', 'warning':'yellow', 'passed':'green'}
    #colors = {'new':'#74D4FF' , 'error': '#FFA2A2', 'warning': '#FFF085', 'passed': '#7BF1A8'}
    colors = {'new':'#3498DB' , 'error': '#E74C3C', 'warning': '#F4D03F', 'passed': '#16A085'}
    if len(idlist) >=1:
        qvars = {'id':idlist[0]}
        query_res = apiQuery(tierselector, dhq.submission_stats_query, qvars)
        columns = ['nodeName', 'total', 'new', 'error', 'warning', 'passed']
        substats_df = pd.DataFrame(columns=columns)
        for entry in query_res['data']['submissionStats']['stats']:
            substats_df.loc[len(substats_df)] = entry
        #Add percentages to df
        calccolumns = columns = ['new', 'error', 'warning', 'passed']
        newcol = ['nodeName', 'new', 'error', 'warning', 'passed']
        per_df = pd.DataFrame(columns=newcol)
        for index, row in substats_df.iterrows():
            newrow = {}
            newrow['nodeName'] = row['nodeName']
            for column in calccolumns:
                if row['total'] > 0:
                    newrow[column] = (row[column]/row['total'])*100
                else:
                    newrow[column] = 0
            per_df.loc[len(per_df)] = newrow

        return px.bar(per_df, x='nodeName', y=['new', 'error', 'warning', 'passed'], color_discrete_map=colors)
    else:
        return px.bar()

    

####################################
#                                  #
#         Run Program              #
#                                  #
####################################


#app.run_server(port=8050, debug=True)
if __name__ == "__main__":
    app.run(port=8050, debug=True)