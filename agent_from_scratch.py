import openai
import re
import httpx
import os
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient

load_dotenv() 

client = OpenAI()
# connect
tavily_client = TavilyClient("tvly-*****")   # Update with your key



system_prompt = """
You run in a loop of Thought, Action, PAUSE, Observation.
At the end of the loop you output an Answer
Use Thought to describe your thoughts about the question you have been asked.
Use Action to run one of the actions available to you - then return PAUSE.
Observation will be the result of running those actions.
CRITICAL: You must always format your actions as 'Action: tool_name: input'

Your available actions are:

calculate:
e.g. calculate: 4 * 7 / 3
Runs a calculation and returns the number - uses Python so be sure to use floating point syntax if necessary

average_dog_weight:
e.g. average_dog_weight: Collie
returns average weight of a dog when given the breed

tavily_search:
Given a user question this tool fetches information form the internet
e.g. What is the weather in Munich
returns: data related to the current weather from a particular place or location,  here for Munich

Example session:

Question: How much does a Bulldog weigh?
Thought: I should look the dogs weight using average_dog_weight
Action: average_dog_weight: Bulldog
PAUSE

You will be called again with this:

Observation: A Bulldog weights 51 lbs

You then output:

Answer: A bulldog weights 51 lbs
""".strip()


class Agent:
    def __init__(self, system=""):
        self.system = system
        self.messages = []  #  this the converation memory of your
        if self.system:
            self.messages.append({"role":"system", "content": system})

    def __call__(self, message):
        self.messages.append({"role":"user", "content": message})
        result = self.execute()
        self.messages.append({"role":"assistant", "content":result})
        return result

    def execute(self):
        completion = client.chat.completions.create(
                        model="gpt-4.1-nano", 
                        temperature=0,
                        messages=self.messages)
        return completion.choices[0].message.content
    
#  Tool No. 1 #  "1+1" 5*7
def calculate(what):
    return eval(what)

#  Tool No. 2
def average_dog_weight(name):
    if name in "Scottish Terrier": 
        return("Scottish Terriers average 20 lbs")
    elif name in "Border Collie":
        return("a Border Collies average weight is 37 lbs")
    elif name in "Toy Poodle":
        return("a toy poodles average weight is 7 lbs")
    else:
        return("An average dog weights 50 lbs")

#  Tool No. 3
def tavily_search(question):
    return tavily_client.search(
    query=question,
    search_depth="advanced"
)
    

known_actions = {
    "calculate": calculate,
    "average_dog_weight": average_dog_weight,
    "tavily_search": tavily_search,
}

# This version is case-insensitive and handles trailing whitespace or extra colons
action_re = re.compile(r'Action:\s*(\w+):\s*(.*)', re.IGNORECASE)

        
def query(question, max_turns =5):
    i=0 
    bot = Agent(system_prompt)
    next_prompt = question
    while i < max_turns:
        i = i + 1
        # now send the next prompt, which is the question
        result = bot(next_prompt)
        print(result)

        actions = [
            action_re.match(a) 
            for a in result.split('\n') 
            if action_re.match(a)
        ]

        if actions:
            # There is an action to run
            action, action_input = actions[0].groups()
            if action not in known_actions:
                raise Exception("Unknown action: {}: {}".format(action, action_input))
            print(" -- running {} {}".format(action, action_input))

            observation = known_actions[action](action_input)

            print("Observation:", observation)

            next_prompt = "Observation: {}".format(observation)
        else:
            return
        
#query("How much does a toy poodle weigh?")

#query("find the box office collection of the movie durandhar 2")

query("find today weather of Munich and Bangalore")
#abot = Agent(system_prompt)


