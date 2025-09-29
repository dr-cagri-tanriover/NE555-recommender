import os
import sys
from google.adk.agents import LlmAgent

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")))
from utils.file_loader import load_instructions_file

circuit_search_agent = LlmAgent(
    name = "circuit_search_agent",
    model = "gemini-2.5-flash",
    instruction=load_instructions_file("agents/circuit_search/instructions.txt"),
    description=load_instructions_file("agents/circuit_search/description.txt"),
    output_key="circuit_search_output"
)