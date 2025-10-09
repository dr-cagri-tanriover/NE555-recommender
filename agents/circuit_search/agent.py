import os
import sys
from google.adk.agents import LlmAgent
from google.adk.tools import google_search, AgentTool, FunctionTool

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")))
from utils.file_loader import load_instructions_file
from utils.config import Config
from tools.page_checker import multi_url_validation

appconfig = Config()  # Object for global application configuration parameter access.

url_seeker_agent = LlmAgent(
    name = "UrlSeeker",
    model = appconfig.llm_model_name,
    instruction="""
    Search and find relevant URLs based on the given query and provide a list of candidate URLs as your output.
    Return ONLY the following JSON object: {"candidate_urls": ["https://...", "https://...", ...]}

    Requirements:
    - Provide unique, high-quality URLs (avoid spam, home pages, and tag/category pages).
    - Prioritize diverse URLs that lead to distinct circuit designs. Avoid listing multiple URLs that essentially point to the same circuit description or variation (e.g. multiple URLs from the same domain describing the same circuit).
    - Do not include any other text.
    """.strip(),
    description="Finds relevant URLs based on the input query using Google search.",
    tools=[google_search],
    output_key="candidate_urls"
)

# AgentTool wrapper for google_search tool to be used inside another agent
UrlSeeker = AgentTool(url_seeker_agent)

###################################

#multi_url_validation_tool = FunctionTool(multi_url_validation, name="MultiUrlValidator", description="Validates a list of URLs and returns only the valid ones.")
MultiUrlValidator = FunctionTool(multi_url_validation)


url_validation_agent = LlmAgent(
    name = "url_validation_agent",
    model = appconfig.llm_model_name,
    instruction="""
    You will receive a JSON payload with:
    {"candidate_urls": ["https://...", "https://...", ...]} 
    
    Call the tool "MultiUrlValidator" with the provided arguments.

    Return ONLY the following JSON object:
    {"validated_urls": ["https://...", "https://...", ...]}

    Requirements:
    - Only include the items returned by the "MultiUrlValidator" tool in your output.
    - Do not include any other text.
    """.strip(),
    description="Processes a list of URLs and validates them to return a subset of valid URLs.",
    #tools=[multi_url_validation_tool],
    tools=[MultiUrlValidator],
    output_key="validated_urls"
)

# AgentTool wrapper for a custom tool to be used inside another agent (with google_search tool)
#ValidationTool = AgentTool(url_validation_agent, name="ValidationTool", description="Used for validating a list of URLs.")
ValidationTool = AgentTool(url_validation_agent)

####################################

web_search_agent = LlmAgent(
    name = "web_search_agent",
    model = appconfig.llm_model_name,
    instruction="""
    Perform a web search based on the given query and deliver your output as markdown.
    """.strip(),
    description="Performs online information search using Google search tool.",
    tools=[google_search]
)

# AgentTool wrapper for google_search tool to be used inside another agent
#SearchTool = AgentTool(web_search_agent, name="SearchTool", description="Used for delivering web search results based on an input query.")
SearchTool = AgentTool(web_search_agent)

###################################

# THE ORCHESTRATOR AGENT FOLLOWS:
# The circuit_search_agent will use the above wrapped agents as part of its tools to perform the required tasks.
circuit_search_agent = LlmAgent(
    name = "circuit_search_agent",
    model = appconfig.llm_model_name,
    instruction=load_instructions_file("agents/circuit_search/instructions.txt"),
    description=load_instructions_file("agents/circuit_search/description.txt"),
    tools=[UrlSeeker, ValidationTool, SearchTool],  # Using AgentTool wrapped tools for compatibility
    output_key="circuit_search_output"
)
