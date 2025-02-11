# Copyright (c) 2024, WSO2 LLC. (https://www.wso2.com/) All Rights Reserved.
from typing import Tuple, Dict, List, Any
from xml.dom.minidom import Document

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
from langchain.chains.question_answering.map_reduce_prompt import messages
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chains.llm import LLMChain
from langchain.chains.question_answering.refine_prompts import chat_qa_prompt_template
from langchain.chains.summarize.map_reduce_prompt import prompt_template
from langchain.evaluation.scoring.prompt import SYSTEM_MESSAGE
from langchain_core.messages import ToolMessage
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
from numpy.f2py.crackfortran import verbose
from langchain_openai import AzureOpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector
from sqlalchemy.testing.suite.test_reflection import metadata
from tenacity import retry_unless_exception_type
from typing import List, Tuple
from utils.prompt_template import template
from api_docs import get_central_api_docs
import os
import json
import re


load_dotenv()

embedding = AzureOpenAIEmbeddings(
    model="text-embedding-3-small",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    openai_api_version="2023-07-01-preview",
    deployment=os.getenv("AZURE_DEPLOYMENT")
)

vector_store = PGVector(
    embeddings= embedding,
    connection=os.getenv("CONNECTION_STRING"),
    collection_name=os.getenv("COLLECTION")
)

llm = AzureChatOpenAI(
    azure_deployment=os.getenv("LLM_DEPLOYMENT"),
    api_version="2023-07-01-preview",
    temperature=0
)


@tool
def extract_learn_pages(query: str) -> list[Document]:
    """Retrieves information about Ballerina language concepts, features, tools, and implementation details from the Ballerina Learn Pages. This includes guidance on syntax, usage, best practices, and examples for addressing various use cases.

    Args:
        query: A question or query requiring information about Ballerina language concepts, features, tools, best practices, or practical use cases related to implementing solutions using the language.
    """

    retrieved_documents = vector_store.similarity_search(query=query, k=6)

    return retrieved_documents


@tool
def extract_central_api_docs(query: str) -> list[dict[str,str]]:
    """Retrieves technical details about Ballerina libraries, modules, clients, functions, type definitions, parameters, return types, and records.

    Args:
        query: A question or query requiring information about Ballerina libraries, including clients, functions, constructors, type definitions, parameters, and return types
    """
    return get_central_api_docs(query)


tools = [extract_learn_pages, extract_central_api_docs]

# prompt = ChatPromptTemplate.from_messages([
#                 ("system", "You are an AI assistant specialized in answering questions about the Ballerina programming language. Your task is to provide accurate and helpful answers based solely on the information retrieved from the tools provided. These tools retrieve information from reliable sources to answer questions related to Ballerina. Do not include any links in your response."),
#                 ("human", "{input}"),
#                 ("placeholder","{agent_scratchpad}"),
#             ])



# this is the implementation to test the tool calls
async def assistant_tool_call(question: str):
    llm_with_tools = llm.bind_tools(tools)
    ai_msg = llm_with_tools.invoke([HumanMessage(question)])
    print("ai message: ", ai_msg.tool_calls)
    tools_to_execute = ai_msg.tool_calls

    central_context = []
    documentation_context = []

    print(tools_to_execute)

    for tool in tools_to_execute:
        if tool['name'] == "extract_learn_pages":
            documentation_context.extend(extract_learn_pages.invoke(tool['args']['query']))
        elif tool['name'] == "extract_central_api_docs":
            central_context.extend(extract_central_api_docs.invoke(tool['args']['query']))

    doc_chunks = {}
    if len(documentation_context) != 0:
        for i in range(len(documentation_context)):
            doc_chunks[f"chunk{i + 1}"] = documentation_context[i]

    llm_message = [
        SystemMessage(
            content= f"""You are an AI assistant specialized in answering questions about the Ballerina programming language. Your task is to provide precise, accurate, and helpful answers based solely on the information provided below. The information provided below comes from reliable and authoritative sources on the Ballerina programming language.
    
    INFORMATION SOURCES:
    
    {f'Information from Ballerina Learn Pages: This section includes content sourced from the Ballerina Learn pages, consisting of document chunks that cover various topics. These chunks also include sample code examples that are necessary for explaining concepts effectively. Out of the given documents, you must include the chunk number(eg:- chunk1,chunk2...) of all the documents that you used to formulate the response within <doc_id></doc_id> tags and include it to the end of your response.Additionally, provide your reasoning for selecting these documents over others from the retrieved set, clearly explaining why they were relevant to the generated response, and enclose this reasoning within <thinking></thinking> tags before the final response." {doc_chunks}' if len(documentation_context) != 0 else ""}
    
    {f'Information from the Ballerina API Documentation:This section provides detailed information about type definitions, clients, functions, function parameters, return types, and other library-specific details essential for answering questions related to the Ballerina programming language. {central_context}' if len(central_context) != 0 else ""}
    
    ADDITIONAL INSTRUCTIONS
    - The response generated must only be based on the information sources provided. 
    - Do not make assumptions when answering questions as answers should be reliable.
    - Do not include any links in the response."""
        ),
        HumanMessage(
            content=question
        )
    ]


    print("This is the llm message: ", llm_message)

    llm_response = llm.invoke(llm_message)
    library_links = []
    if len(central_context) != 0:
        for lib in central_context:
            library_links.append(lib["library_link"])

    doc_ids = []
    doc_id_pattern = r"<doc_id>(.*?)</doc_id>"
    doc_ids.extend(re.findall(doc_id_pattern, llm_response.content))
    print("id list: ", doc_ids)
    filtered_response = re.sub(doc_id_pattern, "", llm_response.content).strip()

    for id in list(doc_chunks.keys()):
        if id in doc_ids:
            library_links.append(doc_chunks[id].metadata["doc_link"])

    formatted_link = ['<' + link + '>' for link in library_links]
    response_content = filtered_response + f"  \nreference sources:  \n" + "  \n".join(formatted_link)
    print("Response content: ", response_content)
    return response_content



# Below is the execution for the agentic RAG
# async def doc_assistant_chat(question):
#     agent = create_tool_calling_agent(llm,tools,prompt)
#     agent_executor = AgentExecutor(agent=agent,tools=tools,verbose=True)
#     print("Question: ", question)
#     result = agent_executor.invoke({"input": question})
#     #print("Answer: ", result.get('output'))
#     return result.get('output')


#THE IMPLEMENTATION BELOW IS FOR A GENERAL RAG APPLICATION


# async def assistant_chat(question: str) -> str:
#     docs = vector_store.similarity_search(query=question, k=6)
#
#     prompt = PromptTemplate.from_template(template)
#     message = prompt.invoke({"question": question, "context": str(docs)})
#
#     print("LLM message: ", message)
#     print("\n")
#     response = llm.invoke(message)
#     print("LLM Response: ", response.content)
#     return response.content


