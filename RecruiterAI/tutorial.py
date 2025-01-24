import requests
import time
import json
# Headers
import os
from dotenv import load_dotenv
load_dotenv()
headers = {
    'authorization': "YOUR_BLAND_API_KEY",
    'Content-Type': 'application/json'
}

# Data
data = {
    'phone_number': 'YOUR_PHONE_NUMBER',
    # The pathway ID can be found in the url of your pathway
    'pathway_id': 'YOUR_PATHWAY_ID',
    'version': 0,
    'language': 'en',
    # Pick a voice
    'voice': 'derek',
    'background_track': "office",
    # Pick a model. Turbo will use the most credits.
    'model': "turbo",
    # Customize the request data to fit your pathway
    'request_data': {
        'firstName': 'Michael',
        'lastName': 'Porter',
        'role': "Head of Logistics",
        'years': 5,
        'experience': "head of procurement"
    }
}

# Create the call
response = requests.post('https://api.bland.ai/v1/calls', json=data, headers=headers)
call_data = response.json()

print("Call created:")
print(call_data)

# Get the call_id from the initial response
call_id = call_data.get('call_id')

# Function to get call details
def get_call_details(call_id):
    url = f'https://api.bland.ai/v1/calls/{call_id}'
    response = requests.get(url, headers=headers)
    return response.json()

# Loop to track the conversation
while True:
    call_details = get_call_details(call_id)
    
    # Print the current status
    print(f"Call Status: {call_details.get('queue_status')}")
    
    # Print new transcripts
    transcripts = call_details.get('transcripts', [])
    for transcript in transcripts:
        print(f"User: {transcript['user']}")
        print(f"Text: {transcript['text']}")
        print(f"Created At: {transcript['created_at']}")
        print("---")
    
    # Check if the call is completed
    if call_details.get('queue_status') in ['complete', 'complete_error']:
        print("Call ended.")
        break
    
    # Wait before the next request
    time.sleep(5)  # Wait for 5 seconds before the next request
