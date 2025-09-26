import os
import sys
from google.adk.agents import SequentialAgent

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")))
from utils.file_loader import load_instructions_file
from agents.requirements_writer.agent import requirements_writer_agent
from agents.circuit_search.agent import circuit_search_agent
from agents.results_writer.agent import results_writer_agent

root_agent = SequentialAgent(
    name="root_ne555_recommender_agent",
    sub_agents=[requirements_writer_agent, circuit_search_agent, results_writer_agent],
    description=load_instructions_file("agents/root_ne555_recommender/description.txt")
)