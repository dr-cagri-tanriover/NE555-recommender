# --- A. IMPORTING THE NECESSARY TOOLS ---
# 'asyncio' is a Python library that helps run multiple tasks at the same time.
import asyncio
import json
from typing import Any
from rich import print as rprint    # Enhanced print function to support colors and formatting
from rich.syntax import Syntax      # Used to highlight JSON output in the terminal

# These are specific classes from Google's AI library for structuring messages.
from google.genai.types import Content, Part

from dotenv import load_dotenv
load_dotenv()

# --- B. IMPORTING OUR AGENT ---
# We are importing the "brain" of our AI agent from our project.
from agents.root_ne555_recommender.agent import root_agent

# --- C. IMPORTING ADK (AGENT DEVELOPMENT KIT) COMPONENTS ---
# These are special tools from the ADK to run our agent programmatically.
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# --- 1. SETTING UP IDENTIFIERS (CONSTANTS) ---
# We define constant text variables to identify our application and conversation.
APP_NAME = "ne555_circuit_recommender"
USER_ID = "tanriover"
SESSION_ID = "session_chat_loop_1" # A unique ID for this entire chat session.

# --- 2. THE MAIN CHAT LOOP FUNCTION ---
# This async function will set everything up once, then loop to allow for continuous chat.
async def chat_loop():
    """
    Initializes the agent and session, then enters a loop to
    continuously accept user queries and provide agent responses.
    """
    print("NE555 Recommender Agent Chat Session Started.")
    print("Type 'quit', 'exit', or ':q' to end the session.\n")

    # --- SETUP (Done Once) ---
    # The Session Service stores the conversation history (memory).
    session_service = InMemorySessionService()
    # We create the session object that will be used for the entire chat.
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    # The Runner is the engine that executes the agent's logic.
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    # --- THE INTERACTIVE LOOP ---
    # This 'while True' loop will run indefinitely until the user decides to quit.
    while True:
        # Prompt the user for their next message.
        user_query = input("Which 555 project(s) do you have in mind today?: ")

        # Check if the user wants to exit the chat.
        # .lower() makes the text lowercase so "Quit" or "QUIT" also work.
        if user_query.lower() in ["quit", "exit", ":q"]:
            print("Ending chat session. Goodbye!")
            break  # This command exits the 'while' loop.

        # --- Agent Interaction (Inside the Loop) ---
        # Format the user's query into the structure the agent understands.
        new_message = Content(role="user", parts=[Part(text=user_query)])

        # The runner.run_async() method sends the message and gets a stream of events back.
        # Because we are using the SAME runner and session IDs each time, the agent
        # remembers the previous parts of the conversation.
        events = runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=new_message
        )

        # --- Process the Event Stream ---
        # We loop through the agent's "thinking steps" (events) to find the final answer.
        final_response = ""
        i = 0
        async for event in events:
            i+= 1  # Increment the event counter
            # Print each event as it comes in, with a title for clarity.
            # This helps us see the agent's thought process step-by-step.
            print_json_response(event, f"============Event #{i}=============")

            if hasattr(event, "author") and event.author == "code_writer_agent":

                if event.is_final_response():
                    # If the event is a final response, we extract the text.
                    # This is the agent's final answer to the user's query.
                    final_response = event.content.parts[0].text
                    # Print a clean separation for the agent's response.
                    print(f"\nAgent Response:\n------------------------\n{final_response}\n")
                    break # Stop processing events once we have the final answer.



# -----------------------------------------------------------------------------
# Helper: Pretty print JSON objects using syntax coloring
# -----------------------------------------------------------------------------
def print_json_response(response: Any, title: str) -> None:
    # Displays a formatted and color-highlighted view of the response
    print(f"\n=== {title} ===")  # Section title for clarity
    try:
        if hasattr(response, "root"):  # Check if response is wrapped by SDK
            data = response.root.model_dump(mode="json", exclude_none=True)
        else:
            data = response.model_dump(mode="json", exclude_none=True)

        json_str = json.dumps(data, indent=2, ensure_ascii=False)  # Convert dict to pretty JSON string
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)  # Apply syntax highlighting
        rprint(syntax)  # Print it with color
    except Exception as e:
        # Print fallback text if something fails
        rprint(f"[red bold]Error printing JSON:[/red bold] {e}")
        rprint(repr(response))


# --- 3. STARTING THE PROGRAM ---
# This is the entry point that runs our chat loop.
if __name__ == '__main__':
    asyncio.run(chat_loop())