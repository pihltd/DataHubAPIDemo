from shiny import Inputs, Outputs, Session, ui, render,reactive, App
import requests
import pandas as pd
import DH_Queries as dhq
import os


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


####################################
#                                  #
#         Layouts                  #
#                                  #
####################################
tiers_dropdown = ui.input_select(
    id="tierSelect", 
    label = "Tier", 
    choices = {"STAGE":"Stage","DEV2":"Dev2"}, 
    selected = None, 
    multiple = False
)

study_dropdown = ui.input_select(
    id='studySelect',
    label='Studies',
    choices=[],
    selected=None,
    multiple=False
)

submission_dropdown = ui.input_select(
    id='submissionSelect',
    label='Submissions',
    choices=[],
    selected=None,
    multiple=False
)
errors_dropdown = ui.input_select(
    id='errorSelect',
    label='Errors',
    choices=[],
    selected=None,
    multiple=False
)

data_dropdown = ui.input_select(
    id='dataSelect',
    label='Data',
    choices=[],
    selected=None,
    multiple=False
)
sidebar = ui.layout_sidebar(
        ui.sidebar(
            "Select a Tier",
            tiers_dropdown,
            study_dropdown,
            submission_dropdown,
            errors_dropdown,
            data_dropdown,
            bg="#4287f5"
        )
    )


mainpage = ui.navset_card_underline(
    ui.nav_panel(ui.card(ui.output_text("mainpagevalue")),
                ui.card(ui.output_data_frame('studyInfo'))),
)

errorpage = ui.navset_card_underline(
    ui.nav_panel(ui.card(ui.output_data_frame('subInfo'))),
)
datapage = ui.navset_card_underline(
    #ui.nav_panel("DataTable", None),
    title="This is the Data Page"
)

tab_layout = ui.navset_pill(
    ui.nav_panel("Main", mainpage),
    ui.nav_panel("Errors",errorpage),
    ui.nav_panel("Data", datapage)
)

tab_layout2 = ui.navset_pill(
    ui.nav_panel("Main", "mainpage"),
    ui.nav_panel("Errors","errorpage"),
    ui.nav_panel("Data", "datapage")
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
    
    studycolumns = ['_id', 'studyAbbreviation', 'studyName', 'dbGaPID']
    study_df = pd.DataFrame(columns=studycolumns)


    @render.text
    def selectedtier():
        return f"{input.tierSelect()}"
    
    @render.text
    def mainpagevalue():
        return f"{input.tierSelect()}"
    
    @render.text
    @reactive.event(input.tierSelect)
    def studyCall():
        jsonthing = apiQuery(input.tierSelect(), dhq.list_sub_query, {"status":["All"]} )
        return str(jsonthing)
    
    @render.data_frame
    def studyInfo():
        studyjson = apiQuery(input.tierSelect(), dhq.org_query, None, False)
        #columns = ['_id', 'studyAbbreviation', 'studyName', 'dbGaPID']
        #study_df = pd.DataFrame(columns=columns)
        for entry in studyjson['data']['getMyUser']['studies']:
            study_df.loc[len(study_df)] = entry
        return render.DataTable(study_df, editable=False)
    @render.data_frame
    def subInfo():
        fulljson = apiQuery(input.tierSelect(), dhq.list_sub_query, {"status":["All"]})
        sub_df = pd.DataFrame(fulljson['data']['listSubmissions']['submissions'])
        working_df = sub_df.loc[sub_df['_id'] == input.studySelect()]
        return render.DataTable(working_df, editable=False)
    
    @reactive.effect
    def updateStudy():
        study_items = {}
        for index, row in study_df.iterrows():
            study_items[row['_id']] = row['studyAbbreviation']
        ui.update_select(
            "studySelect",
            choices=study_items
        )
    @reactive.effect
    def updateSubmisions():
        submission_items = {}
        fulljson = apiQuery(input.tierSelect(), dhq.list_sub_query, {"status":["All"]})
        sub_df = pd.DataFrame(fulljson['data']['listSubmissions']['submissions'])
        working_df = sub_df.loc[sub_df['_id'] == input.studySelect()]
        for index, row in working_df.iterrows():
            submission_items[row["_id"]] = row['name']
        ui.update_select(
            "submissionSelect",
            choices=submission_items
        )


# https://shiny.posit.co/py/get-started/create-run.html
app = App(app, server)