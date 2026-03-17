from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import os
import logging
import traceback
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


load_dotenv()

from agents.investor_agent import app as agent_graph 

backend = FastAPI(
    title="Investor Finder API",
    description="Simple API for finding investors using LLM + search tools",
)


backend.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # tighten this later 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

backend.mount("/static", StaticFiles(directory="static"), name="static")


class SearchRequest(BaseModel):
    query: str

@backend.post("/api/search")
async def search_investors(req: SearchRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        result = agent_graph.invoke({
            "query": req.query,
            "search_queries": [],
            "search_results": [],
            "final_answer": "",
            "messages": []
        })

        import json 
        try:
            parsed = json.loads(result["final_answer"])
        except Exception as e:
            parsed = {
                "investors": [],
                "count": 0,
                "message": f"Agent returned invalid JSON → {str(e)}"
            }

        return parsed
    
    except Exception as e:
        logger.error("Agent error:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

@backend.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")