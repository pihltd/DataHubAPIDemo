# DataHubAPIDemo
Demonstration scripts and notebooks showing how to use the Data Hub API for data submissions, reporting, and other tasks.

**Note:** All of these scripts will require a Data Hub API key in order to use.  Instructions for obtaining an API token can be found in the [data submission documentation](https://datacommons.cancer.gov/data-submission-instructions)

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
This is a Python Dash application that uses the APIs to create a personal dashboard of your submissions.


## ShinyDashboard.py
Simialr to the SubmissionReportDashboard only uses Python Shiny instead of Dash.


## SubmissionReset.py and SubmissionReset.ipynb
Submissions that are inactive for extended periods of time start generating warning emails and after 180 days get deleted.  The remedy to this situation is to log into the Submission Portal and look at the submission.  However, this gets burdensome if there are a large number of submissions to check.  This script (also in notebook form) will query for all the submissions that are either New or In Progress and will request information from each of them.  This re-sets the inactvitiy timer.  

## WarningAggregator.ipynb and WarningAggregator.py
When updating a submission that has previously been through DataHub, it's possible to get a great number of warnings that data is going to be changed.  Unfortunately, the current Submission Portal interface doesn't have a way to aggregate and display these warnings which can make it difficult and tedious to check.  This script and notebook will aggregate all the warnings in a submission and display alternating old and new lines in a table(notebook) or output a csv file (script).  