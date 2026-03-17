from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import operator
import json
import logging
import re
import os

logger = logging.getLogger(__name__)

from .tools import serp_search
from .prompts import SYSTEM_PROMPT, QUERY_REWRITE_PROMPT


llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.35
)


class AgentState(TypedDict):
    query: str
    search_queries: List[str]
    
    search_results: Annotated[List, operator.add]
    final_answer: str
    messages: Annotated[List, operator.add]


def rewrite_query(state: AgentState) -> AgentState:
    try:
        prompt = ChatPromptTemplate.from_template(QUERY_REWRITE_PROMPT)
        chain = prompt | llm
        response = chain.invoke({"user_query": state["query"]})
        lines = response.content.strip().split("\n")
        queries = [q.strip() for q in lines if q.strip() and len(q) > 10][:4]
    except Exception as e:
        logger.error("rewrite_query failed: %s", e, exc_info=True)
        queries = [state["query"]]   # fall back to the raw user query

    return {"search_queries": queries, "messages": [AIMessage(content=f"Generated {len(queries)} search queries")]}

def perform_searches(state: AgentState) -> AgentState:
    all_results = []

    for q in state["search_queries"]:
        try:
            res = serp_search.invoke({"query": q, "num_results": 10})
            logger.info("Search '%s' → %d results", q, len(res))
            all_results.extend(res)
        except Exception as e:
            logger.error("Search failed for '%s': %s", q, e, exc_info=True)
            all_results.append({"error": str(e)})

    logger.info("Total search results collected: %d", len(all_results))
    return {
        "search_results": all_results,
        "messages": [AIMessage(content=f"Collected {len(all_results)} search results")]
    }

def synthesize_answer(state: AgentState) -> AgentState:
    context = "\n\n".join(
        f"[{i+1}] {r.get('title','')}\n{r.get('link','')}\n{r.get('snippet','')[:400]}..."
        for i, r in enumerate(state["search_results"])
    )
    
    prompt = f"""Using ONLY the search results below, extract real investors/funds that match the original query.
    Original query: {state['query']}
    Search results:
    {context}

    Now return ONLY valid JSON in the exact format from the system prompt.
    Do not add extra text."""
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        logger.info("LLM raw response (first 500 chars): %s", response.content[:500])
        content = response.content.strip()
        content = re.sub(r'^```(?:json)?\s*\n?', '', content)
        content = re.sub(r'\n?```\s*$', '', content).strip()
        parsed = json.loads(content)
        final = json.dumps(parsed, indent=2)
    except Exception as e:
        logger.error("synthesize_answer failed: %s", e, exc_info=True)
        final = json.dumps({
            "investors": [],
            "count": 0,
            "message": f"Could not synthesize answer: {str(e)}"
        })
    
    return {
        "final_answer": final,
        "messages": [AIMessage(content="Synthesized final answer")]
    }

wkflow  = StateGraph(AgentState)

wkflow.add_node("rewrite_query", rewrite_query)
wkflow.add_node("perform_searches", perform_searches)
wkflow.add_node("synthesize", synthesize_answer)

wkflow.set_entry_point("rewrite_query")
wkflow.add_edge("rewrite_query", "perform_searches")
wkflow.add_edge("perform_searches", "synthesize")
wkflow.add_edge("synthesize", END)

app = wkflow.compile()

# if __name__ == "__main__":
#     result = app.invoke({
#         "query": "Fintech investors in India investing $500k–$2M",
#         "search_queries": [],
#         "search_results": [],
#         "final_answer": "",
#         "messages": []
#     })
#     print(result["final_answer"])