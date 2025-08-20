from shiny import App, render, ui

#thingamabob = ui.input_select(
#    "select",  
#    "Select an option below:",  
#    {"1A": "Choice 1A", "1B": "Choice 1B", "1C": "Choice 1C"},  
#)


mainpage = ui.navset_card_underline(
    ui.nav_panel("Main Page",
                 "Value Text",
                 ui.card(
                     'maincard',
                     ui.output_text("mainvalue"))),
    #ui.output_text("value"),
    #title="This is the Main Page"
)

errorpage = ui.navset_card_underline(
    ui.nav_panel("Error Table", None),
    title="This is the Error Page"
)
datapage = ui.navset_card_underline(
    ui.nav_panel("Data Table",None),
    title="This is the Data Page"
)
tab_layout = ui.navset_pill(
    ui.nav_panel("Main", mainpage),
    ui.nav_panel("Errors","errorpage"),
    ui.nav_panel("Data", "datapage")
)

tiers_dropdown = ui.input_select(id="tierSelect", 
                                 label = "Tier", 
                                 choices = {"stage":"Stage","dev2":"Dev2"}, 
                                 selected = None, 
                                 multiple = False)

sidebar = ui.layout_sidebar(
    ui.sidebar(
        tiers_dropdown
    )
)



"""
app_ui = ui.page_fixed(
    ui.input_select(  
        "select",  
        "Select an option below:",  
        {"1A": "Choice 1A", "1B": "Choice 1B", "1C": "Choice 1C"},  
    ),  
    ui.output_text("value"),
)
"""
#app_ui = ui.layout_columns(
#    sidebar,
#    tab_layout,
##    ui.output_text("value"),
#    col_widths=(3,7,2)
#)

app_ui = ui.page_fluid(
    ui.layout_columns(
        sidebar,
        tab_layout,
        ui.output_text("value"),
        col_widths=(3,7,1)
    )
)


def server(input, output, session):
    @render.text
    def value():
        return f"{input.tierSelect()}"
    
    @render.text
    def mainvalue():
        return f"{input.tierSelect()}"

app = App(app_ui, server)