import requests
from pprint import pprint 

url = "https://watifly.in/api/533a7c8a-7e5c-4638-8221-1f609ac88eb0/contact/send-message"



def reply_to_msg(phone_number:str, message:str):
    payload = {
        "phone_number": phone_number,
        "message_body": message
    }
    headers = {"Authorization": "Bearer XccoFLdKUib8bjeL5vLQgEzOneW0w5mW58gyaiX2bL9hF7jN8Q6yPY9w2gVxwINB"}

    response = requests.request("POST", url, json=payload, headers=headers)

    response_json=response.json()

    return response_json


if __name__=="__main__":
    print(reply_to_msg("9424553935","test message 1"))
