from shiny import Inputs, Outputs, Session, ui, render,reactive, App, module
# https://shiny.posit.co/py/docs/modules.html

# Dropdown
#Using the module.ui decorator causes an error since I'm supplying my own ID
#@module.ui
def dropdown_ui(id, label, choices):
    return ui.input_select(
        id=id,
        label=label,
        choices=choices,
        selected=None,
        multiple=True
    )
    
def df_table(id, tablename):
    return ui.navset_card_underline(
        ui.nav_panel(
            ui.card(
                ui.card_header(tablename),
                ui.output_data_frame(id),
                full_screen=True
            )
        )
    )
