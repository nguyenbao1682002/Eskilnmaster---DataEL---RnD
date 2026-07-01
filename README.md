# MLBP
## CSV to DynamoDB Python Script
This Python script reads data from a CSV file and uploads it to a DynamoDB table on AWS. It only uploads the last row from the CSV file.

Prerequisites
Python 3.10
Setup
### 1. Clone the repository

First, clone the repository to your local machine:

git clone

cd MLBP

### 2. Set up a virtual environment
Next, set up a Python virtual environment for the project. This helps manage Python dependencies:

python -m venv env

Activate the virtual environment:
.\env\Scripts\activate

### 3. Install dependencies
With the virtual environment activated, install the project's dependencies:

pip install -r requirements.txt

### 4. Update the CSV file path 
In the Python script, replace path_to_your_file.csv with the actual path to your CSV file

### 5. Create file .bat in windows
Create file .bat in windows with the following content
    @echo off
    cd <path to folder MLBP>
    python readCsvAndUploadData.py

### 6. Create file .vbs in windows
Create file .vbs in windows with the following content:
    Set WshShell = CreateObject("WScript.Shell")
    WshShell.Run "cmd /c <path to file .bat>", 0
    Set WshShell = Nothing

This will upload the last row from your CSV file to your DynamoDB table.

Automating the script with Windows Task Scheduler
To upload data every minute, you can automate the script with the Windows Task Scheduler.
- Open Task Scheduler on Windows and create a new task.
- In the General tab, name the task and set it to run regardless of whether the user is logged on.
- In the Triggers tab, create a new trigger that starts the task every 1 minute.
- In the Actions tab, create a new action that starts a program. The program is python, and the argument is the path to your file .vbs
- In the Conditions and Settings tabs, choose the options that are appropriate for your use case.
- Click OK to create the task.
Now, your Python script will run every minute, uploading the last row from your CSV file to your DynamoDB table.
