import pyodbc
from datetime import datetime
import pandas as pd
import requests
import json
import math
import csv
import time
from configparser import ConfigParser
import logging

# Config logging for write to file 'log.txt'
def config_logging(path_log):
    logging.basicConfig(
        filename=path_log,
        filemode='a',
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

# Create connect python with SQL server
def connectSQL(server_client, database_client):
    server = server_client
    database = database_client
    conn_str = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
    conn = pyodbc.connect(conn_str)
    return conn

# Query from SQL server
def querydata(conn,rows_data):
    cursor = conn.cursor()
    query = """
    SELECT TOP ({num_rows}) [ALIASNAME], [pinststart], [numvalue] FROM [ArchiveDB].[ML].[DataRaw_Buffer]
    ORDER BY [pinststart] DESC;
    """.format(num_rows = rows_data)
    df = pd.read_sql(query, conn)
    cursor.close()
    return df

def read_data(df):
    # Convert pinststart
    df['pinststart'] = pd.to_datetime(df['pinststart'])
    # Tranform data
    pivoted_df = df.pivot(index='pinststart', columns='ALIASNAME', values='numvalue')
    pivoted_df = pivoted_df.reset_index()
    # Creata column for new dataframe
    columns = ['pinststart', '4G1GA01XAC01_NO_AVG', '4G1GA01XAC01_O2_AVG', '4G1GA02XAC01_O2_AVG',
               '4G1GA03XAC01_O2_AVG', '4G1GA04XAC01_O2_AVG', '4G1KJ01JST00_T8401_AVG',
               '4K1KP01DRV01_M2001_EI_AVG', '4K1KP01KHE01_B8701_AVG']
    pivoted_df = pivoted_df[columns]
    # Check and conversion type data
    for column in columns:
        if pivoted_df[column].dtype == float:
            pivoted_df[column] = pivoted_df[column].astype(str)
        elif pivoted_df[column].dtype == object:
            pivoted_df[column] = pd.to_numeric(pivoted_df[column], errors='coerce')

    pivoted_df['date'] = pivoted_df['pinststart'].dt.strftime('%Y-%m-%d')
    pivoted_df['time'] = pivoted_df['pinststart'].dt.strftime('%H:%M:%S')

    query1_max_date = pivoted_df['pinststart'].max().strftime('%Y-%m-%d')
    query1_max_time = pivoted_df['pinststart'].max().strftime('%H:%M:%S')

    pivoted_df.drop('pinststart', axis=1, inplace=True)
    print(pivoted_df)
    # print(pivoted_df['4K1KP01DRV01_M2001_EI_AVG'])
    return pivoted_df,query1_max_date,query1_max_time

# Function to handle out-of-range float values and null values
def handle_out_of_range(value):
    if value is None:
        return 0.0  # Replace with the desired default value
    elif math.isfinite(value):
        return value
    elif math.isnan(value):
        return None
    elif math.isinf(value) and value > 0:
        return float('inf')
    elif math.isinf(value) and value < 0:
        return float('-inf')
    else:
        return None

# Function to upload a single data row to DynamoDB
def upload_row_to_dynamodb(url, body, headers):
    # Check for None values and replace them with a default value
    for key, value in body["payload"].items():
        if value is None:
            body["payload"][key] = 0.0  # Replace with the desired default value
    x = requests.post(url, json=body, headers=headers)
    print("Status API:", x.text)

def read_lastDataTime(path_file_last_csv):
    dateAndTime = pd.read_csv(path_file_last_csv)
    date_value = dateAndTime.at[0, 'query1_max_date']
    time_value = dateAndTime.at[0, 'query1_max_time']
    return date_value, time_value

def write_csv(csv_file, query1_max_date, query1_max_time):
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['query1_max_date', 'query1_max_time'])
        writer.writerow([query1_max_date, query1_max_time])

def config_file():
    # Đọc file config
    config = ConfigParser()
    config.read('getData-ver2\config.txt')
    server_client = config.get('connectSQL','server')
    database_client = config.get('connectSQL','database')
    rows_data = config.get('connectSQL','num_rows_to_select')
    URL = config.get('API','url')
    usr = config.get('authentication','usr')
    password = config.get('authentication','passwrd')
    time_sleep = config.get('Timesleep','timesleep')
    path_log = config.get('config_logging','path_log')
    path_file_last_csv = config.get('file_last_CSV','path_file_csv')
    return server_client, database_client, URL,time_sleep, rows_data, usr, password,path_log, path_file_last_csv

def main():
    
    server_client, database_client, URL, time_sleep, rows_data,usr, password, path_log, path_file_last_csv = config_file()
    config_logging(path_log)
    conn = None
    while True:
        try:
            if conn is None:
                conn = connectSQL(server_client, database_client)

            df = querydata(conn,rows_data)
            csv_file = path_file_last_csv
            pivoted_df, query1_max_date, query1_max_time = read_data(df)
            date_value, time_value = read_lastDataTime(path_file_last_csv)
            url = URL
            headers = {
                "Authorization": json.dumps({"username": usr, "password": password})
            }
            if date_value is not None and time_value is not None:
                if date_value < query1_max_date or (date_value == query1_max_date and time_value < query1_max_time):
                    for index, row in pivoted_df.iterrows():
                        try:
                            data_row = {
                                "action": "raw_db__insert_data",
                                "payload": {
                                    "Date": row["date"],
                                    "Time": row["time"],
                                    "4G1GA01XAC01_NO_AVG": handle_out_of_range(float(row["4G1GA01XAC01_NO_AVG"])),
                                    "4G1GA01XAC01_O2_AVG": handle_out_of_range(float(row["4G1GA01XAC01_O2_AVG"])),
                                    "4G1GA02XAC01_O2_AVG": handle_out_of_range(float(row["4G1GA02XAC01_O2_AVG"])),
                                    "4G1GA03XAC01_O2_AVG": handle_out_of_range(float(row["4G1GA03XAC01_O2_AVG"])),
                                    "4G1GA04XAC01_O2_AVG": handle_out_of_range(float(row["4G1GA04XAC01_O2_AVG"])),
                                    "4G1KJ01JST00_T8401_AVG": handle_out_of_range(float(row["4G1KJ01JST00_T8401_AVG"])),
                                    "4K1KP01DRV01_M2001_EI_AVG": handle_out_of_range(float(row["4K1KP01DRV01_M2001_EI_AVG"])),
                                    "4K1KP01KHE01_B8701_AVG": handle_out_of_range(float(row["4K1KP01KHE01_B8701_AVG"]))
                                }
                            }
                            upload_row_to_dynamodb(url, data_row, headers)
                        except Exception as e:
                            logging.error(f"Error while preparing or uploading data row: {e}, retrying in {time_sleep} seconds.")
                            time.sleep(time_sleep)
                            continue

                    write_csv(csv_file, query1_max_date, query1_max_time)
        except Exception as e:
            logging.error(f"Error during initialization or main loop: {e}, retrying in {time_sleep} seconds.")
            conn = None
        time.sleep(int(time_sleep))

if __name__ == "__main__":
    main()
