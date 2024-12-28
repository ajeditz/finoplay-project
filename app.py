from typing import Dict, List, Tuple, Optional, TypedDict
import sqlite3
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
import json
from pydantic import BaseModel
from DB import DatabaseOperations, setup_database
from dotenv import load_dotenv
import os 
load_dotenv()

class ChatState(TypedDict):
    """State for the chat conversation."""
    input: str
    conversation_history: List[Dict[str, str]]
    candidate_info: Dict
    current_step: str
    form_field: Optional[str]
    response: Optional[str]
    is_form_start: bool  # New flag to track if we're starting the form

def initialize_state(input_text: str) -> ChatState:
    """Initialize the chat state."""
    return ChatState(
        input=input_text,
        conversation_history=[],
        candidate_info={},
        current_step="start",
        form_field=None,
        response=None,
        is_form_start=False
    )

# Chatbot Agent
class RecruitingAgent:
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(api_key=openai_api_key)
        self.db = DatabaseOperations()
        self.form_fields = [
            ("name", "Could you please tell me your full name?"),
            ("email", "What's your email address?"),
            ("phone", "What's your phone number?"),
            ("experience_years", "How many years of experience do you have?"),
            ("current_role", "What is your current role?"),
            ("skills", "What are your key skills and technologies you're proficient in?")
        ]
    
    def create_graph(self):
        workflow = StateGraph(ChatState)
        
        workflow.add_node("start", self._determine_intent)
        workflow.add_node("handle_job_form", self._handle_job_form)
        workflow.add_node("handle_job_inquiry", self._handle_job_inquiry)
        
        workflow.add_conditional_edges(
            "start",
            self._route_intent,
            {
                "job_form": "handle_job_form",
                "job_inquiry": "handle_job_inquiry"
            }
        )
        
        workflow.add_edge("handle_job_form", "handle_job_form")
        workflow.add_edge("handle_job_inquiry", END)
        
        workflow.set_entry_point("start")
        return workflow.compile()
    
    def _determine_intent(self, state: ChatState) -> ChatState:
        # If we're already in form filling mode, continue with it
        if state.get('form_field') and not state.get('is_form_start', False):
            state['current_step'] = "job_form"
            return state

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a recruiting assistant. Determine if the user wants to:
            1. Apply for a job (fill out a job application form)
            2. Inquire about available jobs
            Respond with either 'job_form' or 'job_inquiry'"""),
            ("user", "{input}")
        ])
        
        response = self.llm.invoke(prompt.format(input=state['input']))
        intent = response.content.strip().lower()
        
        if intent == "job_form":
            state['is_form_start'] = True
            state['form_field'] = None
        
        state['current_step'] = intent
        return state

    def _handle_job_form(self, state: ChatState) -> ChatState:
        print("\nDebug - Current state:", {
            'form_field': state.get('form_field'),
            'is_form_start': state.get('is_form_start'),
            'input': state.get('input'),
            'candidate_info': state.get('candidate_info')
        })

        # Start the form if it's the beginning
        if state.get('is_form_start', False):
            state['is_form_start'] = False
            state['form_field'] = 'name'
            state['response'] = "I'll help you apply for a job. Could you please tell me your full name?"
            return state

        # Current form field
        form_field = state.get('form_field')
        candidate_info = state.get('candidate_info', {})

        if not form_field:
            # If no field is set, restart the process
            state['form_field'] = 'name'
            state['response'] = "Let's start the application process. Could you please tell me your full name?"
            return state

        # Process the user's input for the current field
        try:
            # Validate input only for the current field
            if state['input']:
                prompt = ChatPromptTemplate.from_messages([
                    ("system", f"""You are a recruiting assistant collecting the {form_field}.
                    Extract only the {form_field} from the user's message.
                    Respond with only the extracted value, nothing else."""),
                    ("user", "{input}")
                ])
                response = self.llm.invoke(prompt.format(input=state['input']))
                extracted_value = response.content.strip()

                if not extracted_value or extracted_value.lower() in ["n/a", "i don't know", ""]:
                    raise ValueError(f"Invalid input for {form_field}")

                # Store the extracted information
                candidate_info[form_field] = extracted_value
                state['candidate_info'] = candidate_info

                # Clear input for the next question
                state['input'] = None

                # Move to the next field
                current_field_index = next(
                    (i for i, (field, _) in enumerate(self.form_fields) if field == form_field), None
                )
                if current_field_index is not None and current_field_index < len(self.form_fields) - 1:
                    next_field, next_question = self.form_fields[current_field_index + 1]
                    state['form_field'] = next_field
                    state['response'] = f"Great! {next_question}"
                else:
                    # All fields completed, try saving candidate info
                    if self._is_candidate_data_complete(candidate_info):
                        try:
                            if self.db.add_candidate(candidate_info):
                                state['response'] = "Thank you for submitting your application! We'll review it and get back to you soon."
                                state['current_step'] = 'end'
                                state['form_field'] = None
                            else:
                                state['response'] = "There was an error processing your application. Please try again."
                        except Exception as e:
                            state['response'] = f"Error adding candidate: {str(e)}. Please try again."
                            state['form_field'] = 'name'
                    else:
                        state['response'] = "Some required information is missing. Let's start again. Could you tell me your full name?"
                        state['form_field'] = 'name'
            else:
                # Ask again if no input provided
                state['response'] = f"I still need your {form_field}. Could you please provide it?"
        except Exception as e:
            print(f"Error processing field {form_field}: {e}")
            state['response'] = f"I didn't quite get your {form_field}. Could you please provide it again?"

        # Update conversation history
        state['conversation_history'] = state.get('conversation_history', []) + [
            {"role": "human", "content": state['input'] or "<No input provided>"},
            {"role": "assistant", "content": state['response']}
        ]

        return state

    def _route_intent(self, state: ChatState) -> str:
        return state['current_step']


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
    
    # Initialize conversation state
    current_state = initialize_state("")
    
    while True:
        # Get user input
        user_input = input("You: ").strip()
        
        # Check for exit command
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("\nBot: Thank you for using our service. Goodbye!")
            break
            
        try:
            # Update input in current state
            current_state['input'] = user_input
            
            # Get the agent's response
            result = workflow.invoke(current_state)
            
            # Update current state with result
            current_state.update(result)
            
            # Print the response
            print(f"\nBot: {result['response']}\n")
            
            # Check if we've finished the form
            if result.get('current_step') == 'end':
                # Reset the state for the next interaction
                current_state = initialize_state("")
            
        except Exception as e:
            print(f"\nBot: I apologize, but I encountered an error: {str(e)}")
            print("Please try again.\n")

if __name__ == "__main__":
    main()