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

## Key observations/learnings:
#### 1 - <u>Reliability of the produced search results</u>           
This seems to be a function of the LLM model used as well as the content of the instructions.txt files used to guide each agent in the pipeline.

At the time of writing, I tried Google's gemini-2.5-flash, gemini-2.5-flash-lite, gemini-2.0-flash, and gemini-2.0-flash-lite models. 2.5 flash works the best but sometimes access to it can be limited due to bandwidth issues. 2.5 flash lite is the next best model to use. The remaining 2.0 flash models provide comparable results.

By manually modifying the instructions.txt files, I managed to reduce the broken URL references provided by the search agent and improved the relevance of the information provided by the same agent. Therefore, I can confirm investing time into manually improving the (initially) auto-generated instructions.txt files is definitely worthwhile.

That said, I could not reduce the broken link errors to zero despite all my efforts. I also observed that the search agent provides the wrong information when that is based on pdf files rather than URLs. The content of the few pdf files recommended by the agent missed the requested NE555 electronic component and the associated circuits. Therefore, creating an agent that exclusively handles the pdf files as part of the search may be a better and more accurate approach here, which is something I plan to experiment with later on.

One other unexpected behavior I observed is sometimes the pipeline fails to generate and write the html data into a file as explicitly instructed. Upon observing this behavior, simply rerunning the agentic pipeline (without making any modifications) seems to fix this problem. I am not sure why this inconsistency occurs and I will continue to observe the frequency of this issue and see if there is a fix I can apply.
