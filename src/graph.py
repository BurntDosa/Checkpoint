from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from src.agents import CheckpointGenerator
from src.storage import save_checkpoint
from src.vector_db import VectorDB
from src.llm import configure_gemini
import os

# Define the state of the graph
class GraphState(TypedDict):
    diff_content: str
    commit_hash: str
    metadata: dict
    generated_markdown: Optional[str]
    filepath: Optional[str]

# Node: Configuration
def configure_env(state: GraphState):
    configure_gemini()
    return state

# Node: Analysis (DSPy)
def analyze_diff(state: GraphState):
    generator = CheckpointGenerator()
    result = generator(diff_content=state["diff_content"])
    return {"generated_markdown": result.markdown_content}

# Node: Storage
def save_output(state: GraphState):
    filepath = save_checkpoint(state["generated_markdown"], state["commit_hash"])
    return {"filepath": filepath}

# Node: Indexing
def index_output(state: GraphState):
    db = VectorDB()
    db.add_checkpoint(
        checkpoint_id=state["commit_hash"],
        content=state["generated_markdown"],
        metadata=state["metadata"]
    )
    return state

# Build the Graph
workflow = StateGraph(GraphState)

workflow.add_node("configure", configure_env)
workflow.add_node("analyze", analyze_diff)
workflow.add_node("save", save_output)
workflow.add_node("index", index_output)

workflow.set_entry_point("configure")
workflow.add_edge("configure", "analyze")
workflow.add_edge("analyze", "save")
workflow.add_edge("save", "index")
workflow.add_edge("index", END)

app = workflow.compile()
