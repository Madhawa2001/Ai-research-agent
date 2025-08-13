from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
#from langchain_openai import ChatOpenAI
#from langchain_google_genai import ChatGoogleGenerativeAI

from groq import Groq
from langchain_groq import ChatGroq

from dotenv import load_dotenv

import asyncio
import os

load_dotenv()
client = Groq()

completion = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=1,
)

server_params = StdioServerParameters(
    command="npx",
    env = {
        "FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY"),
    },
    args = ["firecrawl-mcp"]
)

async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(model=completion, tools=tools)

            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful research assistant that can scrape websites, crawl pages, and exrtact data using firecrawl tools. Think step by step use appropriate tools to answer the user's question."
                }
            ]

            print("Aviailable tools:",*[tool.name for tool in tools])
            print("="*60)

            while True:
                user_input = input("User: ")
                if user_input == "exit":
                    print("Goodbye!")
                    break
                messages.append({"role": "user", "content": user_input[:175000]})

                try:
                    agent_response = await agent.ainvoke({"messages": messages})
                    ai_message = agent_response["messages"][-1].content
                    print(f"AI: {ai_message}")
                except Exception as e:
                    print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

