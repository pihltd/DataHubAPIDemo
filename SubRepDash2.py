from dash import Dash, html, dcc, dash_table, callback, Output, Input, State
import dash
import dash_bootstrap_components  as dbc
import plotly.express as px
import pandas as pd
import requests
import DH_Queries as dhq
import os
from datetime import datetime, timezone
import time

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
    "margin-right": "12rem",
    "padding": "2rem 1 rem"
}

############################################
#                                          #
#             Components                   #
#                                          #
############################################

sidebar = html.Div( #Whole Sidebar Div
    [
        html.H2("Studies", className="display-4"),
        html.Hr(),
        html.H3("Select a Study", className="display-8"),
        html.Hr(),
        html.Div( #Study Dropdown Div
            className='studydropdown',
            children=[
                dcc.Dropdown(
                    id='studyselector',
                    options=dropDownList(study_df['studyAbbreviation'].unique()),
                    multi=False,
                    value = study_df['studyAbbreviation'].sort_values()[0],
                    style={'backgroundcolor':'1E1E1E'},
                ),
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
            ],
            style={'color':'1E1E1E'}
        ),
    ],
    style=SIDEBAR_STYLE,
)

tableheader = html.Div([
    html.Hr(),
    html.P(
        "Detailed Study Information", className="display-8"
    )
],
    style=CONTENT_STYLE)

errorheader = html.Div(
    [
        html.Hr(),
        html.H2("Error and Warning Details"),
        html.Hr()
    ],
    style=CONTENT_STYLE
)

subgraph = html.Div(
          className='submissionStatusPlot',
          children=[
              html.Hr(),
              html.H2("Submission Status"),
              dcc.Graph(id='submissionstatusplot')
          ],
          style=CONTENT_STYLE  
        )

errorpie = html.Div(
    [
    html.Div(
      dbc.Spinner(html.Div(id='errorspinner'), color="primary")  
    ),
    html.Div(
        #Error Pie Chart
        className='ValidationErrorPieChart',
        children=[
            html.Hr(),
            html.H2("Validation Errors"),
            dcc.Graph(id='validationErrorPie')
        ],
        style={'width':'49%', 'display':'inline-block'},
    
    ),
    html.Div(
        #Warning Pie
        className="ValidationWarningPieChart",
        children=[
            html.Hr(),
            html.H2("Validation Warnings"),
            dcc.Graph(id='validationWarningPie')
        ],
        style={'width':'49%', 'display':'inline-block'},
    ),
    ],
    style=CONTENT_STYLE
)

content = html.Div(id="page-content", style=CONTENT_STYLE)
errorcontent = html.Div(
    [
        html.Div(dbc.Spinner(html.Div(id="errorcontentspinner"), color="secondary")),
        html.Div(id="errorcontent", style=CONTENT_STYLE)
    ]
)
#errorcontent = html.Div(id="errorcontent", style=CONTENT_STYLE)
app.layout = html.Div([sidebar, tableheader, content, subgraph, errorpie, errorheader, errorcontent])


####################################
#                                  #
#         Callbacks                #
#                                  #
####################################


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

@app.callback(
    Output('errorselector', 'options'),
    Input(component_id='subselector', component_property='value')
)
def populateErrorSelector(subselector):
    idlist = sub_df.query("name == @subselector")["_id"].tolist()
    if len(idlist)>=1:
        queryvars = {"submissionID":idlist[0], "severity":"All", "first":-1, "offset":0, "sortDirection": "desc", "orderBy": "displayID"}
        selector_res = apiQuery('STAGE', dhq.summaryQuery, queryvars)
        if selector_res['data']['aggregatedSubmissionQCResults']['total'] == None:
            return []
        else:
            val_df = pd.DataFrame(selector_res['data']['aggregatedSubmissionQCResults']['results'])
            return val_df['title'].unique()
    else:
        return []



@app.callback(
    Output('errorcontent', 'children'),
    Input(component_id='errorselector', component_property='value'),
    State(component_id='subselector', component_property='value')
)
def errorDetailTable(errorselector, subselector):
    #Need the submission ID which I can get using State (State doesn't trigger this callback)
    idlist = sub_df.query("name == @subselector")["_id"].tolist()
    if len(idlist)>=1:
        subvars = {"submissionID":idlist[0], "severity":"All", "first":-1, "offset":0, "sortDirection": "desc", "orderBy": "displayID"}
        sub_res = apiQuery('STAGE', dhq.summaryQuery, subvars)
        if sub_res['data']['aggregatedSubmissionQCResults']['total'] == None:
            return {}
        else:
            
            table_df = pd.DataFrame(sub_res['data']['aggregatedSubmissionQCResults']['results'])
            #Need the code for the error
            errorcode = table_df.query("title == @errorselector")['code'].tolist()[0]
            errorvars = {"id": idlist[0], "severities":"All", "first": -1, "offset": 0, "orderBy":"displayID", "sortDirection":"desc", "issueCode":errorcode}
            detail_res = apiQuery('STAGE', dhq.detailedQCQuery, errorvars)
            columns = ['title', 'description']
            error_df = pd.DataFrame(columns=columns)
            for result in detail_res['data']['submissionQCResults']['results']:
                for error in result['errors']:
                    #the following filter is needed because if an entity has more then one error, all are returned by the system.  That's a feature, not a bug.
                    if error['title'] == errorselector:
                        error_df.loc[len(error_df)] = error
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
                tooltip_duration=None
            )
    else:
        return {}
           
    


@app.callback(
    Output('validationErrorPie', 'figure'),
    Input(component_id='subselector', component_property='value')
)
def validationErrorPieChart(subselector):
    idlist = sub_df.query("name == @subselector")["_id"].tolist()
    if len(idlist)>=1:
        valvars = {"submissionID":idlist[0], "severity":"Error", "first":-1, "offset":0, "sortDirection": "desc", "orderBy": "displayID"}
        val_res = apiQuery('STAGE', dhq.summaryQuery, valvars)
        if val_res['data']['aggregatedSubmissionQCResults']['total'] == None:
            return {}
        else:
            val_df = pd.DataFrame(val_res['data']['aggregatedSubmissionQCResults']['results'])
            return px.pie(val_df, values='count', names='title', hole=.3)
    else:
        return {}


@app.callback(
    Output('validationWarningPie', 'figure'),
    Input(component_id='subselector', component_property='value')
)
def validationWarningPieChart(subselector):
    idlist = sub_df.query("name == @subselector")["_id"].tolist()
    if len(idlist)>=1:
        valvars = {"submissionID":idlist[0], "severity":"Warning", "first":-1, "offset":0, "sortDirection": "desc", "orderBy": "displayID"}
        val_res = apiQuery('STAGE', dhq.summaryQuery, valvars)
        if val_res['data']['aggregatedSubmissionQCResults']['total'] == None:
            return {}
        else:
            val_df = pd.DataFrame(val_res['data']['aggregatedSubmissionQCResults']['results'])
            return px.pie(val_df, values='count', names='title', hole=.3)
    else:
        return {}

@app.callback(
    Output('submissionstatusplot', 'figure'),
    Input(component_id="subselector", component_property="value")
)
def subStatusChart(subselector):
    idlist = sub_df.query("name == @subselector")["_id"].tolist()
    if len(idlist) >= 1:
        qvars = {'id': idlist[0]}
        query_res = apiQuery('STAGE', dhq.submission_stats_query, qvars)
        columns = ['nodeName', 'total', 'new', 'error', 'warning', 'passed']
        substats_df = pd.DataFrame(columns=columns)
        for entry in query_res['data']['submissionStats']['stats']:
            substats_df.loc[len(substats_df)] = entry
    
        return px.bar(substats_df, x='nodeName', y=['new', 'error', 'warning', 'passed'])
    else:
        return {}


@app.callback(
    Output("page-content", "children"),
    [Input(component_id='studyselector', component_property='value')]
)
def populateTable(studyselector):
    table_df = sub_df.loc[sub_df['studyAbbreviation'] == studyselector]
    id='studytable',
    data=table_df.to_dict('records')
    columns=[{"name":e, "id":e} for e in (table_df.columns)]
    return dash_table.DataTable(data=data, 
                                columns=columns, 
                                style_table={'overflowX':'auto'},
                                style_cell={'overflow':'hidden', 'textOverflow':'ellipsis', 'maxWidth':10, 'textAlign':'center'},
                                style_data={'color':'black', 'backgroundColor':'white'},
                                style_data_conditional=[{'if':{'row_index':'odd'}, 'backgroundColor': 'rgb(220,220,220)'}],
                                style_header={'backgroundColor': 'rgb(210,210,210)', 'color':'black', 'fontWeight':'bold', 'textAlign':'center'},
                                tooltip_data=[
                                    {
                                        column:{'value': str(value), 'type':'markdown'}
                                        for column, value in row.items()
                                    } for row in table_df.to_dict('records')
                                ],
                                tooltip_duration=None
                                )
 


@app.callback(
    Output("subselector", "options"),
    [Input(component_id='studyselector', component_property='value')],
)
def populateSubDropdown(studyselector):
    temp_df=sub_df[sub_df['studyAbbreviation'] == studyselector]
    return temp_df['name'].unique()
    

####################################
#                                  #
#         Layout                   #
#                                  #
####################################


#app.run_server(port=8050, debug=True)
if __name__ == "__main__":
    app.run_server(port=8050, debug=True)