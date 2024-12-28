from typing import Dict, List, Tuple, Optional, TypedDict
import sqlite3
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
import json
from pydantic import BaseModel
from dotenv import load_dotenv
import os 
load_dotenv()

# Define the State class
class ChatState(TypedDict):
    """State for the chat conversation."""
    input: str
    conversation_history: List[Dict[str, str]]
    candidate_info: Optional[Dict]
    current_step: str
    response: Optional[str]

def initialize_state(input_text: str) -> ChatState:
    """Initialize the chat state."""
    return ChatState(
        input=input_text,
        conversation_history=[],
        candidate_info={},
        current_step="start",
        response=None
    )

# Database setup
def setup_database():
    conn = sqlite3.connect('recruiting.db')
    cursor = conn.cursor()
    
    # Create candidates table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        experience_years INTEGER,
        skills TEXT,
        current_role TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create jobs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        requirements TEXT,
        location TEXT,
        salary_range TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

# Database operations
class DatabaseOperations:
    def __init__(self, db_path='recruiting.db'):
        self.db_path = db_path
    
    def add_candidate(self, candidate_data: Dict) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO candidates (name, email, phone, experience_years, skills, current_role)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                candidate_data['name'],
                candidate_data['email'],
                candidate_data['phone'],
                candidate_data['experience_years'],
                candidate_data['skills'],
                candidate_data['current_role']
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding candidate: {e}")
            return False
        finally:
            conn.close()
    
    def get_active_jobs(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM jobs WHERE is_active = 1')
        jobs = cursor.fetchall()
        conn.close()
        
        return [{
            'id': job[0],
            'title': job[1],
            'description': job[2],
            'requirements': job[3],
            'location': job[4],
            'salary_range': job[5]
        } for job in jobs]

# Chatbot Agent
class RecruitingAgent:
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(api_key=openai_api_key)
        self.db = DatabaseOperations()
        
    def create_graph(self):
        # Define the states and workflow
        workflow = StateGraph(ChatState)
        
        # Define the nodes
        workflow.add_node("start", self._determine_intent)
        workflow.add_node("handle_job_form", self._handle_job_form)
        workflow.add_node("handle_job_inquiry", self._handle_job_inquiry)
        
        # Add edges
        workflow.add_conditional_edges(
            "start",
            self._route_intent,
            {
                "job_form": "handle_job_form",
                "job_inquiry": "handle_job_inquiry"
            }
        )
        
        # Add end edges
        workflow.add_edge("handle_job_form", END)
        workflow.add_edge("handle_job_inquiry", END)
        
        workflow.set_entry_point("start")
        return workflow.compile()
    
    def _determine_intent(self, state: ChatState) -> ChatState:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a recruiting assistant. Determine if the user wants to:
            1. Apply for a job (fill out a job application form)
            2. Inquire about available jobs
            Respond with either 'job_form' or 'job_inquiry'"""),
            ("user", "{input}")
        ])
        
        response = self.llm.invoke(prompt.format(input=state['input']))
        intent = response.content.strip().lower()
        
        state['current_step'] = intent
        return state
    
    def _route_intent(self, state: ChatState) -> str:
        return state['current_step']
    
    def _handle_job_form(self, state: ChatState) -> ChatState:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a recruiting assistant collecting job application information.
            Extract the following information in JSON format:
            {
                "name": "",
                "email": "",
                "phone": "",
                "experience_years": 0,
                "skills": "",
                "current_role": ""
            }
            If any information is missing, ask for it politely."""),
            ("user", "{input}")
        ])
        
        # Add conversation history to help with context
        history = state['conversation_history']
        full_input = "\n".join([msg['content'] for msg in history] + [state['input']])
        
        response = self.llm.invoke(prompt.format(input=full_input))
        try:
            candidate_data = json.loads(response.content)
            if self._is_candidate_data_complete(candidate_data):
                if self.db.add_candidate(candidate_data):
                    state['response'] = "Thank you for submitting your application! We'll review it and get back to you soon."
                else:
                    state['response'] = "There was an error processing your application. Please try again."
            else:
                missing_fields = self._get_missing_fields(candidate_data)
                state['response'] = f"Could you please provide your {', '.join(missing_fields)}?"
                state['candidate_info'].update(candidate_data)
        except json.JSONDecodeError:
            state['response'] = "I couldn't process your information. Could you please provide your details again?"
        
        state['conversation_history'].append({"role": "assistant", "content": state['response']})
        return state
    
    def _handle_job_inquiry(self, state: ChatState) -> ChatState:
        jobs = self.db.get_active_jobs()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a recruiting assistant. Create a natural response about available jobs.
            Format each job in a clear, conversational way. Here are the jobs: {jobs}"""),
            ("user", "{input}")
        ])
        
        response = self.llm.invoke(prompt.format(input=state['input'], jobs=jobs))
        state['response'] = response.content
        state['conversation_history'].append({"role": "assistant", "content": state['response']})
        return state
    
    @staticmethod
    def _is_candidate_data_complete(data: Dict) -> bool:
        required_fields = ['name', 'email', 'phone', 'experience_years', 'skills', 'current_role']
        return all(data.get(field) for field in required_fields)
    
    @staticmethod
    def _get_missing_fields(data: Dict) -> List[str]:
        required_fields = ['name', 'email', 'phone', 'experience_years', 'skills', 'current_role']
        return [field for field in required_fields if not data.get(field)]

# Example usage
def main():
    # Setup database
    setup_database()
    
    # Initialize agent
    agent = RecruitingAgent(os.getenv("OPENAI_API_KEY"))
    workflow = agent.create_graph()
    
    print("Welcome to the Recruiting Chatbot! (Type 'quit' to exit)")
    print("You can:")
    print("1. Apply for a job by saying something like 'I want to apply for a job'")
    print("2. Ask about available jobs by saying something like 'What jobs are available?'")
    print("\n")
    
    while True:
        # Get user input
        user_input = input("You: ").strip()
        
        # Check for exit command
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("\nBot: Thank you for using our service. Goodbye!")
            break
            
        try:
            # Initialize state for this turn of conversation
            current_state = initialize_state(user_input)
            
            # Get the agent's response
            result = workflow.invoke(current_state)
            
            # Print the response
            print(f"\nBot: {result['response']}\n")
            
        except Exception as e:
            print(f"\nBot: I apologize, but I encountered an error: {str(e)}")
            print("Please try again.\n")

if __name__ == "__main__":
    main()