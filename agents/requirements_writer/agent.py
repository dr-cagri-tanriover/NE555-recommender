import os
import sys
from google.adk.agents import LlmAgent

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")))
from utils.file_loader import load_instructions_file
from utils.config import Config

appconfig = Config()  # Object for global application configuration parameter access.

requirements_writer_agent = LlmAgent(
    name = "requirements_writer_agent",
    model = appconfig.llm_model_name,
    instruction=load_instructions_file("agents/requirements_writer/instructions.txt"),
    description=load_instructions_file("agents/requirements_writer/description.txt"),
    output_key="requirements_writer_output"
)