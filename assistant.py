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

def job_inquiry(natural_language_query):
    # Use GPT-4 to generate SQL query from natural language
    prompt = f"""Translate the following natural language query into a SQL statement for a SQLite database with a JobPostings table (columns are 'title', 'description', 'location', 'date_posted'): 
    Use LIKE operator wherever you need to match strings'{natural_language_query}'"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    sql_query = response.choices[0].message.content.strip()
    # print(sql_query)

    # Execute the generated SQL query
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query)
        results = cursor.fetchall()
        conn.close()
        if results:
            return format_results_for_response(results)
        else:
            return "No job postings match your query."
    except sqlite3.Error as e:
        conn.close()
        return f"An error occurred: {e}"

def format_results_for_response(results):
    response = "Here are the job postings matching your query:\n"
    for row in results:
        response += f"Title: {row[0]}\nLocation: {row[1]}\nDescription: {row[2]}\n\n"
    return response

def main():
    print("Welcome to the Recruitment Assistant. Type 'exit' to end the conversation.\n")
    
    #PROMPT should be more detailed for finoplay
    conversation_history = [
        {"role": "system", "content": "You are a recruitment assistant."}
    ]

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break

        conversation_history.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model="gpt-4",
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
                            "natural_language_query": {"type": "string", "description": "User's job inquiry in natural language"}
                        },
                        "required": ["natural_language_query"]
                    }
                }
            ],
            function_call="auto"
        )

        message = response.choices[0].message
        if message.function_call:
            function_name = message.function_call.name
            function_args = json.loads(message.function_call.arguments)

            if function_name == "fill_form":
                result = fill_form(function_args)
            elif function_name == "job_inquiry":
                # print(function_args['natural_language_query'])
                result = job_inquiry(function_args['natural_language_query'])
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
