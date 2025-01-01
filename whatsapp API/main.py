from flask import Flask, request
from pprint import pprint
from reply import reply_to_msg

app=Flask(__name__)

@app.route('/',methods=['POST'])
def webhook():
    req=request.get_json(force=True)
    pprint(req)
    #Extract necessary fields like phone_number, message and media from the request
    phone_number=req.get('contact',{}).get('phone_number')
    is_new_msg=req.get('message',{}).get('is_new_message')

    #Make a function for interacting with this openai assistant, and the function should have a parameter for entering the session ID, such that with the same session ID, the session state should remain consistent
    #i.e. if I enter the same ID, the conversation should pick  at the same point where I left. and if I enter a new ID, a new session should be started 

    #Send it to the openai chatbot
    #Send the openai response back 
    if is_new_msg:
        openai_response="Response from openAI"
        reply_to_msg(phone_number,openai_response)

    return ""


if __name__=="__main__":
    app.run(debug=True, port=9000)
