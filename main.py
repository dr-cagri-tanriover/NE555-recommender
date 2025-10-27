
# main.py

import os
import sys
import json # Import JSON library
import asyncio
from google.genai.types import Content, Part
from google.adk.runners import Runner 
from google.adk.sessions import InMemorySessionService
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"..")))

from utils.file_loader import load_instructions_file
from utils.json_manipulations import write_to_json_file
from agents.root_ne555_recommender.agent import root_agent
from agents.requirements_writer.agent import requirements_writer_agent
from agents.circuit_search.agent import circuit_search_agent
from agents.results_writer.agent import results_writer_agent
from tools.file_writer_tool import write_to_file # Import the tool's function directly

# FOLLOWING IS TO ENSURE GOOGLE API KEY IS RETRIEVED FROM .env FILE. (NEEDED WHEN NOT USING adk web)
from dotenv import load_dotenv
load_dotenv()  # if you keep the key in a .env file

def preview_text(t, n=200):
    return (t[:n].replace("\n"," ") + ("…" if len(t) > n else "")) if t else ""

async def test_agent_pipeline():
    # Test the root_agent with a sample query

    session_service = InMemorySessionService()  # Create ONE session store in pysical memory (will hold all shared and unshared session IDs of this execution pipeline internally)

    APP_NAME="ne555_recommender"
    USER_ID = "tanriover"
    SESSION_ID = "ne555_session"

    # 0) Create the session once (and optionally seed state)
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state={}  # e.g., {"must_contain": "hazard ratio"}
    )

    # Need to create a Runner for each agent
    req_runner = Runner(agent=requirements_writer_agent,
                        app_name=APP_NAME,
                        session_service=session_service)


    # 1. Get User Query (You can replace this with direct input or a config file)
    #user_query = input("Enter your 555 project query: ")
    user_query = "Provide a 200 word overview of the 555 timer chip"

    # Query needs to be converted into Content type first
    user_message = Content(role="user",
                           parts=[Part(text=user_query)]
                           )
    
    events = req_runner.run_async(user_id=USER_ID,
                                   session_id=SESSION_ID,
                                   new_message=user_message
                                )

    i = 0
    async for event in events:
        i += 1
        print(f"\n=== Event #{i} ===")
        print(f"Event ID: {event.id}")

        # Pretty-print depending on event kind
        if hasattr(event, "content") and event.content and len(event.content.parts) > 0:
            part = event.content.parts[0]
            if hasattr(part, "text") and part.text:
                print("Text:", part.text)
            else:
                print("Non-text part:", part.model_dump_json(indent=2))
        else:
            print("Event data:", event.model_dump_json(indent=2))

        # Detect and show the final response
        if hasattr(event, "is_final_response") and event.is_final_response():
            print("\n--- FINAL RESPONSE ---")
            print(event.content.parts[0].text)
            break


    # Need to call session_service after the complete run to capture the final state accurately.
    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    print(f"FINAL PIPELINE STATE:")
    print(f"{session.state}")
    # Also dump the Python dictionary session.state to a JSON file for visual debugging afterwards
    write_to_json_file('./output/final_state.json', session.state)


async def core_agent_pipeline():
    """
    Top level execution pipeline fpor the NE555 Recommender.
    """
    session_service = InMemorySessionService()  # Create ONE session store in pysical memory (will hold all shared and unshared session IDs of this execution pipeline internally)

    APP_NAME="ne555_recommender"
    USER_ID = "tanriover"
    SESSION_ID = "ne555_recommender_session"

    # 0) Create the session once (and optionally seed state)
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state={}    # Initialize any user defined state variables for sharing between agents within the session, if needed e.g., {"must_contain": "hazard ratio"}
                    # DO NOT pre-initialize the key strings of the sub_agent outputs here as this may lead to confusion of the sub_agents and state updates !!!
    )

    ROOT_AGENT_NAME = "root_ne555_recommender_agent" # The top level orchestrator agent

    # Need to create a Runner for each agent
    root_agent_runner = Runner(agent=root_agent,
                        app_name=APP_NAME,
                        session_service=session_service)


    # 1. Get User Query (You can replace this with direct input or a config file)
    # This query is a basic user defined one for the requirements_writer_agent.
    #user_query = input("Enter your 555 project query: ")
    user_query = "provide 2 NE555 circuits that include LED or sound as its output. Each circuit \
                should have a maximum of 10 electronic components excluding the power and \
                associated components such as connectors. The provided circuits should also be \
                beginner friendly in terms of construction on a breadboard."

    # Query needs to be converted into Content type first
    user_message = Content(role="user",
                           parts=[Part(text=user_query)]
                           )
    
    events = root_agent_runner.run_async(user_id=USER_ID,
                                   session_id=SESSION_ID,
                                   new_message=user_message
                                )

    i = 0
    async for event in events:
        i += 1
        author_name = getattr(event, "author", None) # name of the agent/author that generated the event in the pipeline
        print(f"\n=== Event #{i} time: {event.timestamp} event source: {author_name} ===")
        #print(f"Event ID: {event.id}")  # Not very useful alpha-numeric identifier!
        #print(f"Available event keys: {list(event.model_dump().keys())}")  # Very useful for understanding the event keys

        # Show parts with types
        parts = getattr(event, "content", None).parts if getattr(event, "content", None) else []
        if parts:
            print("parts:")
            for idx, p in enumerate(parts):
                p_dict = p.model_dump() if hasattr(p, "model_dump") else dict(p)
                p_type = p_dict.get("type") or p_dict.get("kind") or list(p_dict.keys())[0]
                snippet = preview_text(getattr(p, "text", None))
                print(f"  [{idx}] type={p_type} text={snippet}")
                if p_type == "function_call":
                    # Helpful to see which tool and args
                    fc = p_dict.get("function_call", p_dict)
                    print("     -> tool:", fc.get("name"), "args:", fc.get("arguments"))
        else:
            print("no parts on this event")

        # Tool envelopes, if any
        if getattr(event, "actions", None):
            print("actions:", event.actions)

        print("turn_complete:", getattr(event,"turn_complete",None),
            "finish_reason:", getattr(event,"finish_reason",None))

        if getattr(event, "turn_complete", False):
            session = await session_service.get_session(APP_NAME, USER_ID, SESSION_ID)
            print("STATE KEYS:", list(session.state.keys())) 

        """
        # Pretty-print depending on event kind
        if hasattr(event, "content") and event.content and len(event.content.parts) > 0:
            part = event.content.parts[0]
            if hasattr(part, "text") and part.text:
                print("Text::", part.text)
            else:
                print("Non-text part::", part.model_dump_json(indent=2))
        else:
            print("Event data::", event.model_dump_json(indent=2))
        """
            
        # Detect and show the final response
        if hasattr(event, "is_final_response") and event.is_final_response() and author_name == ROOT_AGENT_NAME:
            # Each sub-agent will create its own final response. We need to break ONLY AFTER the last agent's final event!
            print("\n--- FINAL RESPONSE ---")
            print(event.content.parts[0].text)
            break


    # Need to call session_service after the complete run to capture the final state accurately.
    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    print(f"FINAL PIPELINE STATE:")
    print(f"{session.state}")
    # Also dump the Python dictionary session.state to a JSON file for visual debugging afterwards
    write_to_json_file('./output/final_state.json', session.state)

def core_agent_pipeline_OBSOLETE():
    # 1. Get User Query (You can replace this with direct input or a config file)
    user_query = input("Enter your 555 project query: ")

    # 2. Initialize the state dictionary
    state = {}

    # 3. Run the requirements_writer_agent
    print("\n--- Running requirements_writer_agent ---")
    state['requirements_writer_output'] = requirements_writer_agent.run(query=user_query) # Pass user query as input
    print(f"Requirements Writer Output:\n{state['requirements_writer_output']}\n")

    # 4. Run the circuit_search_agent
    print("\n--- Running circuit_search_agent ---")
    state['circuit_search_output'] = circuit_search_agent.run(state=state) # Important: Pass state
    print(f"Circuit Search Output:\n{state['circuit_search_output']}\n")

    # 5. Run the results_writer_agent
    print("\n--- Running results_writer_agent ---")
    #Prepare try statement
    try:
        html_string = results_writer_agent.run(state=state)
        print(f"Results Writer Response value is:\n{html_string}")
    except Exception as error:
        print (f"Results Writer FAILED with error ", error)

    # 6. Write final Html if things works fine
    print ("Writing the html_string to a file now")
    write_to_file(html_string) # You would use write_to_file tool directly

    print("Pipeline execution complete. Check index.html")

if __name__ == "__main__":
    asyncio.run(core_agent_pipeline())  # main agentic pipeline
    #asyncio.run(test_agent_pipeline())  # sandbox stuff