import json
import pandas as pd
import requests
from datetime import datetime
import time

# Define a date parser function
# date_parser = lambda x: datetime.strptime(x, '%m/%d/%y %I:%M %p')

# Function to read the last line from the CSV file
def read_last_line(csv_file):
    # Parse the CSV file and convert datetime field to datetime
    # df = pd.read_csv(csv_file, parse_dates=['pinststart'], date_parser=date_parser)
    df = pd.read_csv(csv_file)
    df['pinststart'] = pd.to_datetime(df['pinststart'])
    last_row = df.tail(1)
    data = last_row.to_dict(orient='records')[0]
    data_copy = data.copy()
    
    # Convert the data types
    for k, v in data_copy.items():
        if isinstance(v, float):
            data[k] = float(str(v))
        elif isinstance(v, pd.Timestamp) and k == 'pinststart':
            data['date'] = v.strftime('%Y-%m-%d')  # split datetime into date
            data['time'] = v.strftime('%H:%M:%S')  # split datetime into time
            del data['pinststart']  # remove the original datetime field
            
    print (data)
    return data

# Function to upload the data to DynamoDB
def upload_to_dynamodb(url, body, headers):
    x = requests.post(url, json=body, headers=headers)
    print("status API",x.text)

# Main function
def main():
    with open('config.json') as config_file:
        config = json.load(config_file)
        csv_file_path = config['csv_file_path']
    data = read_last_line(csv_file_path)
    start_time = time.time()
    
    url = 'https://p0fmhg8ipc.execute-api.ap-southeast-1.amazonaws.com/alpha/data'
    body = {
        "action": "raw_db__insert_data",
        "payload": {
            "Date": data["date"],
            "Time": data["time"],
            "4G1GA01XAC01_NO_AVG": data["4G1GA01XAC01_NO_AVG"],
            "4G1GA01XAC01_O2_AVG": data["4G1GA01XAC01_O2_AVG"],
            "4G1GA02XAC01_O2_AVG": data["4G1GA02XAC01_O2_AVG"],
            "4G1GA03XAC01_O2_AVG": data["4G1GA03XAC01_O2_AVG"],

            "4G1GA04XAC01_O2_AVG": data["4G1GA04XAC01_O2_AVG"],
            "4G1KJ01JST00_T8401_AVG": data["4G1KJ01JST00_T8401_AVG"],
            "4K1KP01DRV01_M2001_EI_AVG": data["4K1KP01DRV01_M2001_EI_AVG"],
            "4K1KP01KHE01_B8701_AVG": data["4K1KP01KHE01_B8701_AVG"]
        }
    }

    headers = {
        "Authorization": json.dumps({"username": "estec-user", "password": "123456"})
    }
    upload_to_dynamodb(url, body, headers)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Thời gian chạy code: {elapsed_time} giây")
if __name__ == "__main__":
    main()