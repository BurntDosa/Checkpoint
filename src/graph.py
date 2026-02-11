from typing import TypedDict, Optional
from concurrent.futures import ThreadPoolExecutor
from langgraph.graph import StateGraph, END
from src.agents import CheckpointGenerator
from src.storage import save_checkpoint
from src.vector_db import VectorDB
from src.llm import configure_mistral
import os

# Define the state of the graph
class GraphState(TypedDict):
    diff_content: str
    commit_hash: str
    metadata: dict
    generated_markdown: Optional[str]
    filepath: Optional[str]

# Thread executor for background indexing
_indexing_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="indexing")

# Node: Configuration
def configure_env(state: GraphState):
    configure_mistral()
    return state

# Node: Analysis (DSPy)
def analyze_diff(state: GraphState):
    generator = CheckpointGenerator()
    result = generator(diff_content=state["diff_content"])
    return {"generated_markdown": result.markdown_content}

# Node: Storage
def save_output(state: GraphState):
    author = state["metadata"].get("author", "Unknown")
    filepath = save_checkpoint(state["generated_markdown"], state["commit_hash"], author=author)
    return {"filepath": filepath}

# Node: Indexing (async background task)
def index_output(state: GraphState):
    """
    Submit indexing to background thread - don't block workflow completion.
    Removes 2-5s embedding time from critical path.
    """
    def _do_indexing():
        try:
            db = VectorDB()
            db.add_checkpoint(
                checkpoint_id=state["commit_hash"],
                content=state["generated_markdown"],
                metadata=state["metadata"]
            )
        except Exception as e:
            # Log errors but don't crash the workflow
            print(f"Warning: Background indexing failed: {e}")
    
    # Submit to background thread, don't wait
    _indexing_executor.submit(_do_indexing)
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
