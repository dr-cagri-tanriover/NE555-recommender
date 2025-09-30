import os
import sys
from google.adk.agents import LlmAgent

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")))
from utils.file_loader import load_instructions_file
from tools.file_writer_tool import write_to_file
from utils.config import Config

appconfig = Config()  # Object for global application configuration parameter access.

results_writer_agent = LlmAgent(
    name = "results_writer_agent",
    model = appconfig.llm_model_name,
    instruction=load_instructions_file("agents/results_writer/instructions.txt"),
    description=load_instructions_file("agents/results_writer/description.txt"),
    tools=[write_to_file]
)