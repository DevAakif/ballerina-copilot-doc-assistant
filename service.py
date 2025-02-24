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

from fastapi import FastAPI, HTTPException
import uvicorn
import logging
from pydantic import BaseModel
from sqlalchemy.util import await_only

from app import assistant_tool_call

app = FastAPI()
app.openapi_version = "3.0.2"

logger = logging.getLogger(__name__)

class Question(BaseModel):
   query: str

# @app.post("/chat")
# async def root(question: Question):
#    return await assistant_chat(question.query)
#
# @app.post("/ask")
# async def get_answer(question: Question):
#     return await doc_assistant_chat(question.query)

# @app.post("/askAssistant")
# async def ask(question: Question):
#     return await assistant_tool_call(question.query)
#
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)


@app.post("/documentation-assistant")
async def ask(question: Question):
    try:
        if not question.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        response = await assistant_tool_call(question.query)
        return {"response": response}
    except HTTPException as http_exc:
        raise http_exc  # Return FastAPI HTTPException directly
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.critical(f"Failed to start server: {e}", exc_info=True)