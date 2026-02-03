# DataHubAPIDemo
Demonstration scripts and notebooks showing how to use the Data Hub API for data submissions, reporting, and other tasks.

**Note:** All of these scripts will require a Data Hub API key in order to use.  Instructions for obtaining an API token can be found in the [data submission documentation](https://datacommons.cancer.gov/data-submission-instructions).  For security reasons, these tokens should be stored as environment variables on your system.  The scripts expect production and stage API keys to be stored in the environment variables PRODAPI and STAGEAPI, respectively.

## DataHubAPIDemo.ipynb
This Jupyter notebooks walks through a basic example of how to do a CRDC submission using the Data Hub APIs.
Topics covered in this notebook include:
- Finding the studies you are approved to submit to
- Creating a new submission or working on an existing submission
- Uploading the data submission templates
- Running the data and metadata validtions
- Reviewing the results from validations
- Final submission, cancellation, or withdrawl of a submission

## DataHubAPIExtras.ipynb
This notebook covers several queries that can provide more detailed information on the status of your submissions such as:
- Listing all the submissions you have
- Getting high-level summary information about a specific submission
- Getting detailed information about specific submissions
- Getting a detailed inventory of the data that you've added to a submission
- Deleting specific information from a submission
- Retrieving a populated configuration file for use in uploading data files with the CLI Upload Tool

## SubmissionReportDashboard.py
This is a Python Dash application that uses the APIs to create a personal dashboard of your submissions.  To use this script, run the script (# python3 SubmissionReportDashboard.py), then launch a browser and navigate to http://localhost:8050.

**Required Python Libraries**
dash, dash_bootstrap_components, plotly, requests, pandas, datetime, pytz


## ShinyDashboard.py
Simialr to the SubmissionReportDashboard only uses Python Shiny instead of Dash.


## WarningAggregator.ipynb and WarningAggregator.py
  


## SubmissionReset.py
This script resets the inactivity timer for all of your **New** or **In Progress submissions** to the current date.

## SubmissionResetGUI.py
This is a graphical version (Python Dash) of the *SubmissionReset.py* script.  Select a tier from the drop-down and a table of your current New and In Progress submissions will be generated.  Select the submissions you wish to reset the inactivity timer on and then click on the *Reset Time on Selected Submissions* button below the table.  Each submission selected will be reset to the current date.

To use, run the script ($ python3 SubmissionResetGUI.py) and then bring up a browser and navigate to http://localhost:8050.

**Required Python Libraries**
dash, dash_bootstrap_components, requests, pandas, datetime, pytz