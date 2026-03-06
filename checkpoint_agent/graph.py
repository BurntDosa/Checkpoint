from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from checkpoint_agent.agents import CheckpointGenerator
from checkpoint_agent.storage import save_checkpoint
from checkpoint_agent.llm import configure_llm

# Define the state of the graph
class GraphState(TypedDict):
    diff_content: str
    commit_hash: str
    metadata: dict
    generated_markdown: Optional[str]
    filepath: Optional[str]

# Node: Configuration
def configure_env(state: GraphState):
    configure_llm()
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

# Build the Graph
workflow = StateGraph(GraphState)

workflow.add_node("configure", configure_env)
workflow.add_node("analyze", analyze_diff)
workflow.add_node("save", save_output)

workflow.set_entry_point("configure")
workflow.add_edge("configure", "analyze")
workflow.add_edge("analyze", "save")
workflow.add_edge("save", END)

app = workflow.compile()
