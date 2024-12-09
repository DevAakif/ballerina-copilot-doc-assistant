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

from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
from app import assistant_chat


app = FastAPI()
app.openapi_version = "3.0.2"

class Question(BaseModel):
   query: str

@app.post("/chat")
async def root(question: Question):
   return await assistant_chat(question.query)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)