from shiny import Inputs, Outputs, Session, ui, render,reactive, App
import requests
import pandas as pd
import DH_Queries as dhq
import os
from ShinyDashboardModules import dropdown_ui, df_table
from datetime import datetime, timezone
from pytz import timezone as tz


### Useful links
# https://shiny.posit.co/py/gallery/


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
    elif tier == 'BUPKIS':
        return("The Bupkis tier has been selected")
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



def bracketParse(parsethis):
    first = parsethis.split("]")
    errorstring = first[1]
    if "[" in errorstring:
        second = errorstring.split("[")
        return second[0]
    else:
        return errorstring
    
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


####################################
#                                  #
#         Layouts                  #
#                                  #
####################################

sidebar = ui.layout_sidebar(
    ui.sidebar(
        "Select a tier to start",
        #ui.input_radio_buttons(
        #    "subStatus",
        #    "Submission Status",
        #    {"active": "Active Submissions", "all":"All Submissions"},
        #    selected='active'
        #),
        ui.input_checkbox_group(
            "subStatus",
            "Submission State",
            ["All","New", "In Progress", "Submitted", "Released", "Completed","Cancelled", "Rejected", "Withdrawn", "Deleted" "Archived"]
        ),
        dropdown_ui("tierSelect", "Tier", {"BUPKIS":"Select a Tier", "STAGE":"Stage","DEV2":"Dev2"}),
        dropdown_ui("studySelect", "Studies", []),
        dropdown_ui("submissionSelect", "Submissions", []),
        dropdown_ui("errorSelect", "Errors", []),
        dropdown_ui("dataSelect", "Data",[]),
        bg="#4287f5"
    )
)

tab_layout=ui.navset_pill(
    ui.nav_panel("Main",df_table("studyInfo", "Submission Information")),
    ui.nav_panel("Errors", df_table("errorSummaryInfo", "Error Summary"), df_table("errorInfo", "Full Error Information")),
    ui.nav_panel("Data", df_table("dataInfo", "Data Information"))
)

app = ui.page_fluid(
    ui.panel_title(ui.h2("CRDC Submission Dashboard")),
    ui.layout_columns(
        sidebar,
        tab_layout,
        #ui.output_text("selectedtier"),
        ui.output_text("studyCall"),
        #col_widths=(3,7,2)
        col_widths=(3,9)
    )    
)

    
    
####################################
#                                  #
#         Run Program              #
#                                  #
####################################
    
def server(input, output, session):
    
    ####################################
    #                                  #
    #        Create DataFrames         #
    #                                  #
    ####################################
    
    # STUDY INFORMATION
    @reactive.calc
    @reactive.event(input.tierSelect, ignore_none=True, ignore_init=True)
    def studyDF():
        studyjson = apiQuery(input.tierSelect(), dhq.org_query, None, False)
        study_df = pd.DataFrame(studyjson['data']['getMyUser']['studies'])
        return study_df
    
    # SUBMISSION INFORMATION
    @reactive.calc
    @reactive.event(input.studySelect, ignore_none=True, ignore_init=True)
    def submissionDF():
        getSubTypes = list(input.subStatus())
        fulljson = apiQuery(input.tierSelect(), dhq.list_sub_query, {"status":getSubTypes})
        sub_df = pd.DataFrame(fulljson['data']['listSubmissions']['submissions'])
        sub_df = elapsedTime(sub_df)
        return sub_df
    
    # FULL ERROR INFORMATION
    @reactive.calc
    @reactive.event(input.errorSelect, ignore_init=True, ignore_none=True)
    def errorDF():
        errorvars = {"id": input.submissionSelect(), "severities":"All", "first": -1, "offset": 0, "orderBy":"displayID", "sortDirection":"desc"}
        fulljson = apiQuery(input.tierSelect(), dhq.detailedQCQuery, errorvars)
        columns = ['type', 'title', 'description']
        error_df = pd.DataFrame(columns=columns)
        for result in fulljson['data']['submissionQCResults']['results']:
            for error in result['errors']:
                if error['title'] == input.errorSelect():
                    desc = bracketParse(error['description'])
                    error_df.loc[len(error_df)] = {'type': 'Error', 'title': error['title'], 'description': desc}
        return error_df
    
    #SUMMARY ERROR INFORMATION
    @reactive.calc
    @reactive.event(input.submissionSelect, ignore_init=True, ignore_none=True)
    def errorSummaryDF():
        columns = ['type', 'title', 'description']
        working_df = pd.DataFrame(columns=columns)
        errorvars = {"id": input.submissionSelect(), "severities":"Error", "first": -1, "offset": 0, "orderBy":"displayID", "sortDirection":"desc"}
        error_res = apiQuery(input.tierSelect(), dhq.detailedQCQuery, errorvars)
        if error_res['data']['submissionQCResults']['total'] > 0:
            for result in error_res['data']['submissionQCResults']['results']:
                for error in result['errors']:
                    message = bracketParse(error['description'])
                    working_df.loc[len(working_df)] = {'type':'Error', 'title':error['title'], 'description':message}
            errorSummary_df = working_df.groupby(['title', 'description']).size().reset_index().rename(columns={0:'count'}).sort_values(by='count', ascending=False)
        else:
            errorSummary_df = pd.DataFrame({'type': ['None'], 'title': ['None'], 'description': ['None']})
        return errorSummary_df
        
    # DATA INFORMATION
    @reactive.calc
    @reactive.event(input.dataSelect, ignore_init=True, ignore_none=True)
    def dataDF():
        queryvars = {'_id':input.submissionSelect(), 'nodeType':input.dataSelect(), 'status':'All', 'first':-1, 'offset':0, 'orderBy':'studyID', 'sortDirection':'desc'}
        data_res = apiQuery(input.tierSelect(), dhq.submission_nodes_query, queryvars)
        if data_res['data']['getSubmissionNodes']['total'] == None:
            data_df = pd.DataFrame({'Data': ['No Data Found']})
        else:
            data_df = pd.DataFrame(data_res['data']['getSubmissionNodes']['nodes'])
        return data_df
        

    @render.text
    def selectedtier():
        return f"{input.tierSelect()}"
    
    @render.text
    def mainpagevalue():
        return f"{input.tierSelect()}"
    
    #@render.text
    #@reactive.event(input.tierSelect, ignore_init=True, ignore_none=True)
    #def studyCall():
        #jsonthing = apiQuery(input.tierSelect(), dhq.list_sub_query, {"status":["All"]} )
        #queryvars = {"submissionID":input.submissionSelect(), "severity":"All", "first":-1, "offset":0, "sortDirection": "desc", "orderBy": "displayID"}
        #jsonthing = apiQuery(input.tierSelect(), dhq.summaryQuery, queryvars)
        #return str(jsonthing)
        #jsonthing = ''.join(input.subSelect())
        #jsonthing = list(input.subSelect())
        #return str(jsonthing)
    
    ####################################
    #                                  #
    #        Update Tables             #
    #                                  #
    ####################################
    
    
    @render.data_frame
    def studyInfo():
        return render.DataGrid(submissionDF(), selection_mode='row')
    
    @render.data_frame
    def errorInfo():
        return render.DataGrid(errorDF(), selection_mode='row')
        
    
    @render.data_frame
    def errorSummaryInfo():
        return render.DataGrid(errorSummaryDF(), selection_mode='row')
    
    @render.data_frame
    def dataInfo():
        return render.DataGrid(dataDF(), selection_mode='row')
    
    
    ####################################
    #                                  #
    #       Update Drop downs          #
    #                                  #
    ####################################
    
    @reactive.effect
    def updateStudy():
        study_items = {}
        for index, row in studyDF().iterrows():
            study_items[row['_id']] = row['studyAbbreviation']
        ui.update_select(
            "studySelect",
            choices=study_items
        )
        
        
    @reactive.effect
    @reactive.event(input.studySelect, ignore_init=True, ignore_none=True)
    def updateSubmisions():
        submission_items = {}
        working_df = submissionDF().loc[submissionDF()['studyID'] == input.studySelect()]
        for index, row in working_df.iterrows():
            submission_items[row["_id"]] = row['name']
        ui.update_select(
            "submissionSelect",
            choices=submission_items
        )
        
    @reactive.effect    
    @reactive.event(input.submissionSelect, ignore_init=True, ignore_none=True)
    def updateErrors():
        error_items = {}
        queryvars = {"submissionID":input.submissionSelect(), "severity":"All", "first":-1, "offset":0, "sortDirection": "desc", "orderBy": "displayID"}
        selector_res = apiQuery(input.tierSelect(), dhq.summaryQuery, queryvars)
        if selector_res['data']['aggregatedSubmissionQCResults']['total'] == None:
            error_items =  {"No Errors": "No Errors"}
        else:
            for entry in selector_res['data']['aggregatedSubmissionQCResults']['results']:
                #error_items[entry['code']] = entry['title']
                error_items[entry['title']] = entry['title']
        ui.update_select(
            "errorSelect",
            choices=error_items,
        )
            
    
    @reactive.effect
    @reactive.event(input.submissionSelect, ignore_init=True, ignore_none=True)
    def updateData():
        data_items = {}
        queryvars = {'id':input.submissionSelect()}
        data_res = apiQuery(input.tierSelect(), dhq.submission_stats_query, queryvars)
        if len(data_res['data']['submissionStats']['stats']) > 0:
            for entry in data_res['data']['submissionStats']['stats']:
                data_items[entry['nodeName']] = entry['nodeName']
        else:
            data_items['No Data'] = 'No Data'
        ui.update_select(
            'dataSelect',
            choices=data_items
        )
        


# https://shiny.posit.co/py/get-started/create-run.html
app = App(app, server)