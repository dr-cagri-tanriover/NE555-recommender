import os
import sys
import logging
from google.adk.agents import LlmAgent
from google.adk.tools import google_search, FunctionTool  # Pre-built tool for Google search functionality

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")))
from utils.file_loader import load_instructions_file
from utils.config import Config
from tools.page_checker import url_valid

appconfig = Config()  # Object for global application configuration parameter access.

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

url_validator = FunctionTool(func=url_valid)

circuit_search_agent = LlmAgent(
    name = "circuit_search_agent",
    model = appconfig.llm_model_name,
    instruction=load_instructions_file("agents/circuit_search/instructions.txt"),
    description=load_instructions_file("agents/circuit_search/description.txt"),
    tools=[google_search, url_validator],  # Google search tool for researching the assigned question
    output_key="circuit_search_output"
)