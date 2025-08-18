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
import time
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
app.title ="DH Dashboard"



#######################################
#                                     #
#       Subroutines                   #
#                                     #
#######################################
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
    first = parsethis.split("]")
    errorstring = first[1]
    if "[" in errorstring:
        second = errorstring.split("[")
        return second[0]
    else:
        return errorstring


def updateAggregation(df):
    filelist = []
    columns = ['title', 'description', 'count']
    agg_df = pd.DataFrame(columns=columns)
    for index, row in df.iterrows():
        if row['title'] == 'Updating existing data':
            if "file_id" in row['description']:
                filelist.append(row['description'])
        else:
            agg_df.loc[len(agg_df)] = row
    if len(filelist) > 0:
        agg_df.loc[len(agg_df)] = {'title': 'Updating existing data', 'description': 'File update', 'count': len(filelist)}
    return agg_df

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
                    options = ['DEV2','STAGE', 'PROD'],
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
    html.H2("Study Information", id='studytabletitle'),
    html.Hr()
],
    style=CONTENT_STYLE)



errorheader = html.Div(
    [
        html.Hr(),
        html.H2("Error and Warning Details", id='errortitle'),
        html.Hr()
    ],
    style=CONTENT_STYLE
)


barcharts = html.Div(
    [
        html.Div(
            dbc.Spinner(html.Div(id='errorspinner'), color="primary")
        ),
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
    ],
    style=CONTENT_STYLE
)



errorpie = html.Div(
    [
    html.Div(
        #Error Pie Chart
        className='ValidationErrorPieChart',
        children=[
            html.Hr(),
            html.H2("Validation Errors", id='validationerrorpietitle'),
            dcc.Graph(id='validationErrorPie')
        ],
        style={'width':'49%', 'display':'inline-block'},
    
    ),
    html.Div(
        #Warning Pie
        className="ValidationWarningPieChart",
        children=[
            html.Hr(),
            html.H2("Validation Warnings", id='validationwarningpietitle'),
            dcc.Graph(id='validationWarningPie')
        ],
        style={'width':'49%', 'display':'inline-block'},
    ),
    ],
    style=CONTENT_STYLE
)

errorsummary = html.Div(
    [
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
    ],
    style={"margin-left": "18rem","margin-right": "12rem","padding": "2rem 1 rem","display": "flex"}
)



dataheader = html.Div(
    [
        html.Hr(),
        html.H2("Submitted Data", id='datatitle'),
        html.Hr()
    ],
    style=CONTENT_STYLE
)

batchheader = html.Div(
    [
        html.Hr(),
        html.H2("Batch History", id="batchtitle"),
        html.Hr()
    ],
    style=CONTENT_STYLE
)

batchcontent = html.Div(
    [
        html.Div(id="batchcontent", style=CONTENT_STYLE)
    ]
)

content = html.Div(id="page-content", style=CONTENT_STYLE)
errorcontent = html.Div(
    [
        html.Div(dbc.Spinner(html.Div(id="errorcontentspinner"), color="primary")),
        html.Div(id="errorcontent", style=CONTENT_STYLE)
    ]
)



datacontent = html.Div(
    [
        html.Div(dbc.Spinner(html.Div(id="datacontentspinner"), color="primary")),
        html.Div(id="datacontent", style=CONTENT_STYLE)
    ]
)



####################################
#                                  #
#         Layouts                  #
#                                  #
####################################


app.layout = html.Div([sidebar,
                       dcc.Tabs(id='tabs-container', value='tab-status',
                                children=
                           [
                               dcc.Tab(label="Status",
                                       value = 'tab-status',
                                       style = TAB_STYLE,
                                       selected_style = SELECTED_TAB_STYLE,
                                       children=[
                                           tableheader, content, barcharts, errorpie, errorsummary
                                       ],
                               ),
                               dcc.Tab(
                                   label="Submission Batch History",
                                   value="tab-batch",
                                   style=TAB_STYLE,
                                   selected_style=SELECTED_TAB_STYLE,
                                   children=[
                                       batchheader, batchcontent
                                   ]
                               ),
                               dcc.Tab(label="Submission Errors",
                                       value = 'tab-errors',
                                       id = 'errortab',
                                       style = TAB_STYLE,
                                       selected_style = SELECTED_TAB_STYLE,
                                       children=[
                                           errorheader, errorcontent
                                       ]
                               ),
                               dcc.Tab(label="Submitted Data",
                                       value = 'tab-data',
                                       style = TAB_STYLE,
                                       selected_style = SELECTED_TAB_STYLE,
                                       children=[
                                           dataheader, datacontent
                                       ]),
                           ],
                           style=CONTENT_STYLE
                       )])



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
    Output('submissionstore', 'data'),
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


#@app.callback(
#    Output('submissionstore', 'clear_data'),
#    Input(component_id='tierselector', component_property='value')
#)
#def clearSubmissionStore(tierselector):
#     return True
    


###################### Spinner Callbacks ##################################



@app.callback(
    Output('datacontentspinner', 'children'),
    Input(component_id='dataselector', component_property='value')
)
def loadDataSpinner(value):
    time.sleep(5)
    return value



@app.callback(
    Output('errorspinner', 'children'),
    Input(component_id='subselector', component_property='value')
)
def loadErrorSpinner(value):
    time.sleep(5)
    return value



@app.callback(
    Output('errorcontentspinner', 'children'),
    Input(component_id='errorselector', component_property='value')
)
def errorDetailSpinner(value):
    time.sleep(5)
    return value



######################## Title callbacks ####################################


@app.callback(
    Output("studytabletitle", "children"),
    Input(component_id='studyselector', component_property='value')
)
def changeStudyTableTitle(studyselector):
    return f"Study Information: {studyselector}"


@app.callback(
    Output("submissionstatusplottitle", "children"),
    Input(component_id='subselector', component_property='value')
)
def changeSubmissionStatusPlotTitle(subselector):
    return f"Submission Status by Count: {subselector}"


@app.callback(
    Output("submissionPercentstatusplottitle", "children"),
    Input(component_id='subselector', component_property='value')
)
def changeSubmissionStatusPercentageTitle(subselector):
    return f"Submission Status by Percentage: {subselector}"


@app.callback(
    Output('validationerrorpietitle', "children"),
    Input(component_id='subselector', component_property='value')
)
def changeValidationErrorPieTitle(subselector):
    return f"Validation Errors: {subselector}"


@app.callback(
    Output('validationwarningpietitle', "children"),
    Input(component_id='subselector', component_property='value')
)
def changeValidationWarningPieTitle(subselector):
    return f"Validation Warnings: {subselector}"


@app.callback(
    Output("errortitle", "children"),
    Input(component_id="errorselector", component_property='value'),
    State(component_id="studyselector", component_property="value"),
    State(component_id="subselector", component_property="value")
)
def errorTableTitle(errorselector, studyselector, subselector):
    return ("Error and Warning Details:",html.Br(),"Study: "+studyselector,html.Br(),"Submission: "+subselector, html.Br(), "Errors: "+errorselector)


@app.callback(
    Output("datatitle", "children"),
    Input(component_id="dataselector", component_property='value'),
    State(component_id="studyselector", component_property="value"),
    State(component_id="subselector", component_property="value")
)
def errorTableTitle(dataselector, studyselector, subselector):
    return ("Submitted Data:",html.Br(),"Study: "+studyselector,html.Br(),"Submission: "+subselector, html.Br(), "Node: "+dataselector)

@app.callback(
    Output("batchtitle", "children"),
    Input(component_id="subselector", component_property="value")
)
def batchTableTitle(subselector):
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
        queryvars = {"submissionID":idlist[0], "severity":"All", "first":-1, "offset":0, "sortDirection": "desc", "orderBy": "displayID"}
        selector_res = apiQuery(tierselector, dhq.summaryQuery, queryvars)
        if selector_res['data']['aggregatedSubmissionQCResults']['total'] == None:
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
    Output("page-content", "children"),
    Input(component_id='studyselector', component_property='value'),
    State(component_id='submissionstore', component_property='data'),
)
def populateStudyInfoTable(studyselector, submissionstore):
    sub_df = pd.read_json(io.StringIO(submissionstore),orient='split')
    table_df = sub_df.loc[sub_df['studyAbbreviation'] == studyselector]
    data=table_df.to_dict('records')
    columns=[{"name":e, "id":e} for e in (table_df.columns)]
    return dash_table.DataTable(data=data, 
                                columns=columns, 
                                style_table={'overflowX':'auto'},
                                style_cell={'overflow':'hidden', 'textOverflow':'ellipsis', 'maxWidth':10, 'textAlign':'center'},
                                style_data={'color':'black', 'backgroundColor':'white'},
                                style_data_conditional=[{'if':{'row_index':'odd'}, 'backgroundColor': 'rgb(220,220,220)'},
                                                        {'if':{'filter_query':'{inactiveDays} <= 45', 'column_id':'inactiveDays'}, 'backgroundColor':'green', 'color':'white'},
                                                        {'if':{'filter_query':'{inactiveDays} >= 46 && {inactiveDays} <=59', 'column_id':'inactiveDays'}, 'backgroundColor':'yellow', 'color':'black'},
                                                        {'if':{'filter_query':'{inactiveDays} >= 60', 'column_id':'inactiveDays'}, 'backgroundColor':'red', 'color':'white'}],
                                style_header={'backgroundColor': 'rgb(210,210,210)', 'color':'black', 'fontWeight':'bold', 'textAlign':'center'},
                                tooltip_data=[
                                    {
                                        column:{'value': str(value), 'type':'markdown'}
                                        for column, value in row.items()
                                    } for row in table_df.to_dict('records')
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
        if data_res['data']['getSubmissionNodes']['total'] == None:
            return {}
        else:
            data_df = pd.DataFrame(columns=data_res['data']['getSubmissionNodes']['properties'])
            for entry in data_res['data']['getSubmissionNodes']['nodes']:
                data_df.loc[len(data_df)] = json.loads(entry['props'])
            return dash_table.DataTable(
                data=data_df.to_dict('records'),
                columns=[{"name": e, "id": e} for e in (data_df.columns)],
                style_table={'overflowX':'auto'},
                style_cell={'overflow':'hidden', 'textOverflow':'ellipsis', 'maxWidth':10, 'textAlign':'center'},
                style_data={'color':'black', 'backgroundColor':'white'},
                style_data_conditional=[{'if':{'row_index':'odd'}, 'backgroundColor': 'rgb(220,220,220)'}],
                style_header={'backgroundColor': 'rgb(210,210,210)', 'color':'black', 'fontWeight':'bold', 'textAlign':'center'},
                tooltip_data=[
                    {
                        column:{'value': str(value), 'type':'markdown'}
                        for column, value in row.items()
                    } for row in data_df.to_dict('records')
                ],
                tooltip_duration=None,
                export_format="csv"
            )
    else:
        return {}



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
        subvars = {"submissionID":idlist[0], "severity":"All", "first":-1, "offset":0, "sortDirection": "desc", "orderBy": "displayID"}
        sub_res = apiQuery(tierselector, dhq.summaryQuery, subvars)
        if sub_res['data']['aggregatedSubmissionQCResults']['total'] == None:
            return {}
        else:   
            #table_df = pd.DataFrame(sub_res['data']['aggregatedSubmissionQCResults']['results'])
            errorvars = {"id": idlist[0], "severities":"All", "first": -1, "offset": 0, "orderBy":"displayID", "sortDirection":"desc"}
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
                for warning in result['warnings']:
                    if warning['title'] == errorselector:
                        warning['type'] = 'Warning'
                        error_df.loc[len(error_df)] = warning
            return dash_table.DataTable(
                data=error_df.to_dict('records'),
                columns=[{"name":e, "id":e} for e in (error_df.columns)],
                style_table={'overflowX':'auto'},
                style_cell={'overflow':'hidden', 'textOverflow':'ellipsis', 'maxWidth':10, 'textAlign':'center'},
                style_data={'color':'black', 'backgroundColor':'white'},
                style_data_conditional=[{'if':{'row_index':'odd'}, 'backgroundColor': 'rgb(220,220,220)'}],
                style_header={'backgroundColor': 'rgb(210,210,210)', 'color':'black', 'fontWeight':'bold', 'textAlign':'center'},
                tooltip_data=[
                    {
                        column:{'value': str(value), 'type':'markdown'}
                        for column, value in row.items()
                    } for row in error_df.to_dict('records')
                ],
                tooltip_duration=None,
                export_format="csv"
            )
    else:
        return {}


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
        if batch_res['data']['listBatches']['total'] == None:
            return {}
        else:
            batch_df = pd.DataFrame(columns=list(batch_res['data']['listBatches']['batches'][0].keys()))
            for batch in batch_res['data']['listBatches']['batches']:
                batch_df.loc[len(batch_df)] = batch
            #Need to covert errors and files to string otherwise it borks the table
            batch_df['errors'] = batch_df['errors'].astype(str)
            batch_df['files'] = batch_df['files'].astype(str)
            return dash_table.DataTable(
                data=batch_df.to_dict('records'),
                columns=[{"name":e, "id":e} for e in batch_df.columns],
                style_table={'overflowX':'auto'},
                style_cell={'overflow':'hidden', 'textOverflow':'ellipsis', 'maxWidth':10, 'textAlign':'center'},
                style_data={'color':'black', 'backgroundColor':'white'},
                style_data_conditional=[{'if':{'row_index':'odd'}, 'backgroundColor': 'rgb(220,220,220)'}],
                style_header={'backgroundColor': 'rgb(210,210,210)', 'color':'black', 'fontWeight':'bold', 'textAlign':'center'},
                tooltip_data=[
                    {
                        column:{'value': str(value), 'type':'markdown'}
                        for column, value in row.items()
                    } for row in batch_df.to_dict('records')
                ],
                tooltip_duration=None,
                export_format="csv")
    else:
        return {}


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
        subvars = {"submissionID":idlist[0], "severity":"All", "first":-1, "offset":0, "sortDirection": "desc", "orderBy": "displayID"}
        sub_res = apiQuery(tierselector, dhq.summaryQuery, subvars)
        if sub_res['data']['aggregatedSubmissionQCResults']['total'] == None:
            return {}
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
            return dash_table.DataTable(
                data=summary_df.to_dict('records'),
                columns=[{"name":e, "id":e} for e in summary_df.columns],
                style_table={'overflowX':'auto'},
                style_cell={'overflow':'hidden', 'textOverflow':'ellipsis', 'maxWidth':10, 'textAlign':'center'},
                style_data={'color':'black', 'backgroundColor':'white'},
                style_data_conditional=[{'if':{'row_index':'odd'}, 'backgroundColor': 'rgb(220,220,220)'}],
                style_header={'backgroundColor': 'rgb(210,210,210)', 'color':'black', 'fontWeight':'bold', 'textAlign':'center'},
                tooltip_data=[
                    {
                        column:{'value': str(value), 'type':'markdown'}
                        for column, value in row.items()
                    } for row in summary_df.to_dict('records')
                ],
                tooltip_duration=None,
                export_format="csv"
            )
    else:
        return {}



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
        subvars = {"submissionID":idlist[0], "severity":"All", "first":-1, "offset":0, "sortDirection": "desc", "orderBy": "displayID"}
        sub_res = apiQuery(tierselector, dhq.summaryQuery, subvars)
        if sub_res['data']['aggregatedSubmissionQCResults']['total'] == None:
            return {}
        else:
            columns = ['type', 'title', 'description']
            error_df = pd.DataFrame(columns=columns)
            errorvars = {"id": idlist[0], "severities":"Warning", "first": -1, "offset": 0, "orderBy":"displayID", "sortDirection":"desc"}
            detail_res = apiQuery(tierselector, dhq.detailedQCQuery, errorvars)
            for result in detail_res['data']['submissionQCResults']['results']:
                for error in result['warnings']:
                    message = bracketParse(error['description'])
                    error_df.loc[len(error_df)] = {'type':'Error', 'title':error['title'], 'description':message}
            temp_df = error_df.groupby(['title', 'description']).size().reset_index().rename(columns={0:'count'}).sort_values(by='count', ascending=False)
            summary_df = updateAggregation(temp_df)
            summary_df = summary_df.sort_values(by='count', ascending=False)
            return dash_table.DataTable(
                data=summary_df.to_dict('records'),
                columns=[{"name":e, "id":e} for e in summary_df.columns],
                style_table={'overflowX':'auto'},
                style_cell={'overflow':'hidden', 'textOverflow':'ellipsis', 'maxWidth':10, 'textAlign':'center'},
                style_data={'color':'black', 'backgroundColor':'white'},
                style_data_conditional=[{'if':{'row_index':'odd'}, 'backgroundColor': 'rgb(220,220,220)'}],
                style_header={'backgroundColor': 'rgb(210,210,210)', 'color':'black', 'fontWeight':'bold', 'textAlign':'center'},
                tooltip_data=[
                    {
                        column:{'value': str(value), 'type':'markdown'}
                        for column, value in row.items()
                    } for row in summary_df.to_dict('records')
                ],
                tooltip_duration=None,
                export_format="csv"
            )
    else:
        return {}
            
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
    if len(idlist)>=1:
        valvars = {"submissionID":idlist[0], "severity":"Error", "first":-1, "offset":0, "sortDirection": "desc", "orderBy": "displayID"}
        val_res = apiQuery(tierselector, dhq.summaryQuery, valvars)
        if val_res['data']['aggregatedSubmissionQCResults']['total'] == None:
            return {}
        else:
            val_df = pd.DataFrame(val_res['data']['aggregatedSubmissionQCResults']['results'])
            return px.pie(val_df, values='count', names='title', hole=.3)
    else:
        return {}



@app.callback(
    Output('validationWarningPie', 'figure'),
    Input(component_id='subselector', component_property='value'),
    State(component_id='submissionstore', component_property='data'),
    State(component_id='tierselector', component_property='value'),
)
def validationWarningPieChart(subselector, submissionstore, tierselector):
    sub_df = pd.read_json(io.StringIO(submissionstore),orient='split')
    idlist = sub_df.query("name == @subselector")["_id"].tolist()
    if len(idlist)>=1:
        valvars = {"submissionID":idlist[0], "severity":"Warning", "first":-1, "offset":0, "sortDirection": "desc", "orderBy": "displayID"}
        val_res = apiQuery(tierselector, dhq.summaryQuery, valvars)
        if val_res['data']['aggregatedSubmissionQCResults']['total'] == None:
            return {}
        else:
            val_df = pd.DataFrame(val_res['data']['aggregatedSubmissionQCResults']['results'])
            return px.pie(val_df, values='count', names='title', hole=.3)
    else:
        return {}



@app.callback(
    Output('submissionstatusplot', 'figure'),
    Input(component_id="subselector", component_property="value"),
    State(component_id='submissionstore', component_property='data'),
    State(component_id='tierselector', component_property='value'),
)
def subStatusChart(subselector, submissionstore, tierselector):
    sub_df = pd.read_json(io.StringIO(submissionstore),orient='split')
    idlist = sub_df.query("name == @subselector")["_id"].tolist()
    if len(idlist) >= 1:
        qvars = {'id': idlist[0]}
        query_res = apiQuery(tierselector, dhq.submission_stats_query, qvars)
        columns = ['nodeName', 'total', 'new', 'error', 'warning', 'passed']
        substats_df = pd.DataFrame(columns=columns)
        for entry in query_res['data']['submissionStats']['stats']:
            substats_df.loc[len(substats_df)] = entry
        return px.bar(substats_df, x='nodeName', y=['new', 'error', 'warning', 'passed'])
    else:
        return {}



@app.callback(
    Output("submissionPercentstatusplot", "figure"),
    Input(component_id="subselector", component_property="value"),
    State(component_id="submissionstore", component_property="data"),
    State(component_id="tierselector", component_property="value")
)
def subStatusPercentageChart(subselector, submissionstore, tierselector):
    sub_df = pd.read_json(io.StringIO(submissionstore),orient='split')
    idlist = sub_df.query("name == @subselector")["_id"].tolist()
    if len(idlist) >=1:
        qvars = {'id':idlist[0]}
        query_res = apiQuery(tierselector, dhq.submission_stats_query, qvars)
        columns = ['nodeName', 'total', 'new', 'error', 'warning', 'passed']
        substats_df = pd.DataFrame(columns=columns)
        for entry in query_res['data']['submissionStats']['stats']:
            substats_df.loc[len(substats_df)] = entry
        #Add percentages to df
        calccolumns = columns = ['new', 'error', 'warning', 'passed']
        newcol = ['nodeName', 'new_percentage', 'error_percentage', 'warning_percentage', 'passed_percentage']
        per_df = pd.DataFrame(columns=newcol)
        for index, row in substats_df.iterrows():
            newrow = {}
            newrow['nodeName'] = row['nodeName']
            for column in calccolumns:
                if row['total'] > 0:
                    newrow[column+'_percentage'] = (row[column]/row['total'])*100
                else:
                    newrow[column+'_percentage'] = 0
            per_df.loc[len(per_df)] = newrow

        return px.bar(per_df, x='nodeName', y=['new_percentage', 'error_percentage', 'warning_percentage', 'passed_percentage'])
    else:
        return {}

    

####################################
#                                  #
#         Run Program              #
#                                  #
####################################


#app.run_server(port=8050, debug=True)
if __name__ == "__main__":
    app.run(port=8050, debug=True)