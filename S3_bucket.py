# Import the necessary libraries
import json
import os
import boto3
from datetime import datetime
# Import other modules of project directory
from dotenv import load_dotenv

load_dotenv()

# Load the environment variables
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
bucket_name = os.getenv("S3_BUCKET_NAME")

# Create a client object for S3
s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)


def download_last_modified_file_from_s3(prefix=None, industry=None, state=None):
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if 'Contents' in response:
            # Sort objects by LastModified timestamp in descending order
            objects = sorted(response['Contents'], key=lambda obj: obj['LastModified'], reverse=True)
            # Download only the latest file
            for obj in objects:
                key = obj['Key']
                txt = s3.get_object(Bucket=bucket_name, Key=key)
                data = json.loads(txt['Body'].read().decode('utf-8'))
                if data['industry'] == industry and data['state'] == state:
                    last_modified_file = json.dumps({
                        "category": data['category'],
                        "response": data['response'],
                        "sources": data['sources'],
                        "industry": data['industry'],
                        "state": data['state'],
                        "date": datetime.now().date().strftime("%Y-%m-%d")
                    })
                    return last_modified_file
            return None
        else:
            print("No objects found in the given prefix.")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def get_file_from_s3(prefix):
    count = 2
    prefix = f"archive/{prefix}"
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if 'Contents' in response:
            # Sort objects by LastModified timestamp in descending order
            objects = sorted(response['Contents'], key=lambda obj: obj['LastModified'], reverse=True)
            # Download the recent files according to count
            recent_files = []
            for obj in objects[1:count+1]:
                key = obj['Key']
                txt = s3.get_object(Bucket=bucket_name, Key=key)
                recent_files.append(json.loads(txt['Body'].read().decode('utf-8')))
            return recent_files
        else:
            print("No objects found in the given prefix.")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def upload_file_to_s3(data, category, industry, state):
    try:
        key = f"archive/{category}/{(datetime.now())}.json"
        #     upload data as a file to S3 bucket
        formatted_data = json.dumps({
            "response": data,
            "industry": industry,
            "state": state,
            "date": datetime.now().date().strftime("%Y-%m-%d"),
        })
        s3.put_object(Bucket=bucket_name, Key=key, Body=formatted_data)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
