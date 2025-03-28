# DataHubAPIDemo
Demonstration scripts and notebooks showing how to use the Data Hub API for data submissions

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
- Requires a DataHub API token to retrieve data
