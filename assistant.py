from openai import OpenAI
import sqlite3
import json
import  os 
from dotenv import  load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Initialize OpenAI API key

# Function to handle form filling
def fill_form(details):
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO Candidates (name, email, phone, resume_link)
    VALUES (?, ?, ?, ?)
    ''', (details['name'], details['email'], details['phone'], details['resume_link']))
    conn.commit()
    conn.close()
    return "Your application has been submitted successfully."

# Function to handle job inquiries
def job_inquiry(query):
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    cursor.execute('''
    SELECT title, description, location
    FROM JobPostings
    WHERE title LIKE ? OR description LIKE ?
    ''', (f'%{query}%', f'%{query}%'))
    jobs = cursor.fetchall()
    conn.close()
    if jobs:
        return format_jobs_for_response(jobs)
    else:
        return "No job postings match your query."

# Function to format job postings for response
def format_jobs_for_response(jobs):
    response = "Here are the job postings matching your query:\n"
    for job in jobs:
        response += f"Title: {job[0]}\nLocation: {job[2]}\nDescription: {job[1]}\n\n"
    return response

# Main function to handle continuous conversation
def main():
    print("Welcome to the Recruitment Assistant. Type 'exit' to end the conversation.\n")
    conversation_history = [
        {"role": "system", "content": "You are a recruitment assistant who helps candidates by either helping them to fill out application by asking their details in a natural converstaion or  by answering job-related queries"}
    ]

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break

        conversation_history.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(model="gpt-4",
        messages=conversation_history,
        functions=[
            {
                "name": "fill_form",
                "description": "Collect candidate details and insert into the Candidates table.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Candidate's full name"},
                        "email": {"type": "string", "description": "Candidate's email address"},
                        "phone": {"type": "string", "description": "Candidate's phone number"},
                        "resume_link": {"type": "string", "description": "Link to candidate's resume"}
                    },
                    "required": ["name", "email", "phone", "resume_link"]
                }
            },
            {
                "name": "job_inquiry",
                "description": "Fetch job postings based on user query.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "User's job inquiry"}
                    },
                    "required": ["query"]
                }
            }
        ],
        function_call="auto")

        message = response.choices[0].message
        if message.function_call:
            function_name = message.function_call.name
            function_args = json.loads(message.function_call.arguments)
            # Process the function call as needed

            if function_name == "fill_form":
                result = fill_form(function_args)
            elif function_name == "job_inquiry":
                result = job_inquiry(function_args['query'])
            else:
                result = "I'm sorry, I don't understand that request."

            conversation_history.append({"role": "assistant", "content": result})
            print(f"Assistant: {result}\n")
        else:
            assistant_reply = message.content.strip()
            conversation_history.append({"role": "assistant", "content": assistant_reply})
            print(f"Assistant: {assistant_reply}\n")

if __name__ == "__main__":
    main()
