# NE555-recommender
This project is an AI agent based application designed to make recommendations on NE555 based circuits based on user specifications. The project uses Google ADK as agentic AI framework.

## Useful tips:
#### 1 - <u>Google API key:</u>
In order to work with Google AI APIs, you will need to generate a private API key by visiting [this link](https://aistudio.google.com/app/api-keys) After you generate your key <u>*DO NOT share it with anyone or make it public via GitHub !*</u>

You also need to create a .env text file and include the following two lines in it.

GOOGLE_API_KEY= ***copy & paste your private key here***
GOOGLE_GENAI_USE_VERTEXAI=FALSE

> Be sure to add .env file to your .gitignore in order to protect your private API key by NOT pushing it to GitHub publicly !!

#### 2 - <u>Generating instructions.txt:</u>
Each agent depends on a detailed instructions.txt file in order to execute a designated task as required. Rather than writing this text file manually, it is good to use an LLM agent to create a file with all the required details. You can use any LLM agent or [Google's Gemini](https://aistudio.google.com/app/prompts/new_chat?model=gemini-2.5-flash "Gemini ChatBot") to create the instructions.txt file. This file can be manually edited as needed as part of the user review process.

