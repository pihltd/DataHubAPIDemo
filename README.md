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

## DeleTron.py
This script addresses a weakness in the Submission Portal, namely that deleting some, but not all, entries in a node can become tedious.  The graphical interface nicely supports deleting individual entries as well as entire nodes.  However, the graphical interface does not support deleting dozens or hundreds of entries if needed.

DeleTron.py will take a Data Hub csv loading sheet and instead of adding the information to the submission, it will **delete** all the entries from the submission.  This allows a submitter to start with one of their existing loading sheets, edit it down (or copy to a new load sheet) the entires they wish deleted.  Like submission, deletion works on a node-by-node basis and a separate deletion sheet has to be provided for each node to be deleted.

### Note:
Data Hub will also delete any child nodes that are orphaned by deleting a parent.  For example, if a sample is orphaned when a participant is deleted, the sample will also be deleted even though a sample load sheet was never provided.  For this reason it's usually useful to understand the existing relationships before deleting and exploring if updating the information would be a better approach.

DeleTron requires a yaml file with the following parameters.  It is recommended you start with the *delete_configs.yml* example:
- **tier**: The Data Hub tier you wish to use.  Likely either *stage* or *prod*
- **deletefile**: The full path to the file that contains the information to be deleted.
- **submissionid**: The UUID for the submission you are editing.  This can be copied from the upper left of the submission view in the GUI.
- **node**: The node you will be deleting informaiton from.  For example *file*, *diagnosis*, or *participant*

There is additional required information in the **mdffiles** section that should not be edited.  If you create your own yaml configuration file, make sure this section is copied over and not edited.