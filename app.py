# Copyright (c) 2024, WSO2 LLC. (https://www.wso2.com/) All Rights Reserved.

# WSO2 LLC. licenses this file to you under the Apache License,
# Version 2.0 (the "License"); you may not use this file except
# in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.

from langchain.agents import create_tool_calling_agent, AgentExecutor, initialize_agent, AgentType
from langchain.chains.llm import LLMChain
from langchain.chains.question_answering.refine_prompts import chat_qa_prompt_template
from langchain.chains.summarize.map_reduce_prompt import prompt_template
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
from numpy.f2py.crackfortran import verbose
from langchain_openai import AzureOpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector
from utils.prompt_template import template
import psycopg
import psycopg2
import os

load_dotenv()

embeddings = AzureOpenAIEmbeddings(
    model="text-embedding-3-small",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    openai_api_version="2023-07-01-preview",
    deployment="text-embed"
)

vector_store = PGVector(
    embeddings= embeddings,
    connection=os.getenv("CONNECTION_STRING"),
    collection_name="learn-pages"
)


# @tool
# def extract_learn_pages(query: str) -> str:
#     """Answer questions and queries relevant to Ballerina language concepts, usage, features, tools, and use cases
#
#     Args:
#         query: question or query related to Ballerina language concepts, usage, features, tools, or use cases
#     """
#
#     retrieved_documents = vector_store.similarity_search(query=query, k=6)
#     return str(retrieved_documents)
#
#
# @tool
# def extract_central_api_docs(query: str) -> str:
#     """Answer questions and queries requiring detailed information from Ballerina Central API docs, including libraries, type definitions, functions, parameters, return types, and their descriptions
#
#     Args:
#         query: question or query related to libraries, type definitions, functions, parameters, and return types
#     """
#     return "Executed the second function"
#
# llm = AzureChatOpenAI(
#     azure_deployment="gpt4o-mini",
#     api_version="2023-07-01-preview",
#     temperature=0
# )
# tools = [extract_learn_pages, extract_central_api_docs]
#
# prompt = ChatPromptTemplate.from_messages([
#                 ("system", "You are a helpful AI bot"),
#                 ("human", "{input}"),
#                 ("placeholder","{agent_scratchpad}"),
#             ])
#
#
# agent = create_tool_calling_agent(llm,tools,prompt)
# agent_executor = AgentExecutor(agent=agent,tools=tools,verbose=True)
#
# query = "can you show me some examples from the ballerina examples on azure"
# print("Question: ", query)
# result = agent_executor.invoke({"input": query})
# print("Answer: ", result)



# THE IMPLEMENTATION BELOW IS FOR A GENERAL RAG APPLICATION

llm = AzureChatOpenAI(
    azure_deployment="gpt4o-mini",
    api_version="2023-07-01-preview",
    temperature=0
)

async def assistant_chat(question: str) -> str:
    docs = vector_store.similarity_search(query=question, k=6)
    for document in docs:
        print("Document: ", document)

    prompt = PromptTemplate.from_template(template)
    message = prompt.invoke({"question": question, "context": str(docs)})

    print("LLM message: ", message)
    print("\n")
    response = llm.invoke(message)
    return response.content
