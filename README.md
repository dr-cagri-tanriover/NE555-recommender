# NE555-recommender
This project is an AI agent based application designed to make recommendations on NE555 based circuits based on user specifications. The project uses Google ADK as agentic AI framework.

You can specify details of how you want the agent to explore the timer circuits as part of your prompt including the total number of circuits you would like to have, the high level features of the circuits (e.g., include an LED, sound, waveform etc. as output), number of components each circuit should have, how advanced each circuit be etc.

## Useful tips:
#### 1 - <u>Google API key:</u>           
In order to work with Google AI APIs, you will need to generate a private API key by visiting [this link](https://aistudio.google.com/app/api-keys) After you generate your key <u>*DO NOT share it with anyone or make it public via GitHub !*</u>

You also need to create a .env text file and include the following two lines in it.   
GOOGLE_API_KEY= ***copy & paste your private key here***   
GOOGLE_GENAI_USE_VERTEXAI=FALSE

> Be sure to add .env file to your .gitignore in order to protect your private API key by NOT pushing it to GitHub publicly !!

#### 2 - <u>Generating instructions.txt:</u>   
Each agent depends on a detailed instructions.txt file in order to execute a designated task as required. Rather than writing this text file manually, it is good to use an LLM agent to create a file with all the required details. You can use any LLM agent or [Google's Gemini](https://aistudio.google.com/app/prompts/new_chat?model=gemini-2.5-flash "Gemini ChatBot") to create the instructions.txt file. This file can be manually edited as needed as part of the user review process.

Remember, the quality of the generated result will be as good as the instructions themselves. Therefore, it is good to spend time on improving the content of each instructions.txt file as part of your development. The files I provide in my project should be a good starting point, however, feel free to modify them as I am sure there is plenty of room for improvement on my initial explorations!

#### 3 - <u>How to run the project:</u>   
Make sure your Python virtual environment is activated and that you are inside the project folder on the terminal. Then simply type:
> adk web ./agents

The above will start a server as:   
> http://127.0.0.1:8000

Copy and paste the above into your browser and pick the "root_ne555_recommender" agent from the drop down menu.

Then simply type in your brief prompt on the type of NE555 timer circuits you would like to explore and hit enter. The agents will get to work and deliver their findings as an html file under the output folder, which you can read in your web browser.

Following is a sample prompt I used to give you an idea:   
> "suggest 10 NE555 timer circuits that include LED or sound output or a combination of both. Each circuit should include no more than 10 electronic components and should be beginner friendly."