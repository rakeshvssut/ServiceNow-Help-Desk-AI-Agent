# main.py

import json
from typing import List, TypedDict
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOllama
from langgraph.graph import StateGraph, END
from fastapi import FastAPI
from pydantic import BaseModel
from tools import ServiceNowTool, KnowledgeBaseRetriever
import config

# --- 1. Define Agent State ---
class AgentState(TypedDict):
    ticket_number: str
    ticket_details: str
    candidate_teams: List[dict]
    final_decision: dict
    error: str

# --- 2. Initialize Tools ---
snow_tool = ServiceNowTool()
kb_retriever = KnowledgeBaseRetriever()
llm = ChatOllama(model="llama3", format="json")

# --- 3. Define Agent Nodes ---
def fetch_ticket_data(state: AgentState):
    print("---FETCHING TICKET DATA---")
    details = snow_tool.get_ticket_details(state['ticket_number'])
    return {"error": details} if "Error:" in details else {"ticket_details": details}

def find_candidate_teams(state: AgentState):
    print("---FINDING CANDIDATE TEAMS---")
    candidates = kb_retriever.find_relevant_teams(state['ticket_details'])
    return {"candidate_teams": candidates}

def make_final_decision(state: AgentState):
    print("---MAKING FINAL DECISION---")
    prompt = ChatPromptTemplate.from_template(
        """You are an expert IT Service Desk router. Analyze the ticket and a list of candidate teams to find the single best assignment group. 
        Respond ONLY with a JSON object with three keys: 'best_group_id', 'reasoning', and a 'confidence_score' ('High', 'Medium', or 'Low').
        If no team is a good fit, set best_group_id to null and confidence_score to 'Low'.

        Ticket Details:
        {ticket_details}

        Candidate Teams:
        {candidates}
        """
    )
    chain = prompt | llm
    response_str = chain.invoke({"ticket_details": state['ticket_details'], "candidates": state['candidate_teams']}).content
    try:
        return {"final_decision": json.loads(response_str)}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response from LLM."}

def assign_to_specialist(state: AgentState):
    print("---ASSIGNING TO SPECIALIST TEAM---")
    decision = state['final_decision']
    comment = f"Automatically routed by ATOS Agent.\nReasoning: {decision['reasoning']}"
    snow_tool.reassign_ticket(state['ticket_number'], decision['best_group_id'], comment)
    return {}
    
def assign_to_human_desk(state: AgentState):
    print("---ESCALATING TO HUMAN DESK---")
    comment = "ATOS Agent could not find the proper assignment group, hence we are routing to ATOS Service Desk."
    snow_tool.reassign_ticket(state['ticket_number'], config.HUMAN_DESK_GROUP_ID, comment)
    return {}

def route_decision(state: AgentState):
    """Determines which path to take based on the LLM's confidence."""
    if state.get("error"):
        print(f"Error occurred: {state['error']}")
        return "end"
    
    decision = state.get('final_decision', {})
    if decision.get('confidence_score') == 'High' and decision.get('best_group_id'):
        return "assign_to_specialist"
    else:
        return "assign_to_human_desk"

# --- 4. Build the LangGraph Workflow ---
workflow = StateGraph(AgentState)
workflow.add_node("fetch_ticket_data", fetch_ticket_data)
workflow.add_node("find_candidate_teams", find_candidate_teams)
workflow.add_node("make_final_decision", make_final_decision)
workflow.add_node("assign_to_specialist", assign_to_specialist)
workflow.add_node("assign_to_human_desk", assign_to_human_desk)

workflow.set_entry_point("fetch_ticket_data")
workflow.add_edge("fetch_ticket_data", "find_candidate_teams")
workflow.add_edge("find_candidate_teams", "make_final_decision")
workflow.add_conditional_edges("make_final_decision", route_decision, {
    "assign_to_specialist": "assign_to_specialist",
    "assign_to_human_desk": "assign_to_human_desk",
    "end": END
})
workflow.add_edge("assign_to_specialist", END)
workflow.add_edge("assign_to_human_desk", END)

app_graph = workflow.compile()

# --- 5. Create the FastAPI Server ---
app = FastAPI(title="ATOS Agent Server")

class TicketRequest(BaseModel):
    ticket_number: str

@app.post("/process_ticket")
async def process_ticket(request: TicketRequest):
    inputs = {"ticket_number": request.ticket_number}
    # The .invoke() method runs the graph from start to finish
    result = app_graph.invoke(inputs)
    return {"message": "Ticket processing initiated.", "final_state": result}