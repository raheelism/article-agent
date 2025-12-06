from typing import List, Dict, Annotated, TypedDict
import operator
from app.core.vfs import VFS

# We can't put VFS in a Pydantic model easily if we want it to be mutable and shared efficiently, 
# but for LangGraph state, it needs to be serializable if we use persistence.
# For now, we will treat VFS as a dictionary in the state, or reconstruct it.
# Actually, LangGraph state is usually Pydantic or TypedDict.
# Let's use a TypedDict for the state.

class Task(TypedDict):
    id: int
    description: str
    type: str # 'research' | 'write' | 'review'
    status: str # 'pending' | 'completed' | 'failed'
    params: Dict # extra params

class AgentState(TypedDict):
    # User Inputs
    topic: str
    word_count: int
    language: str
    
    # Execution State
    plan: List[Task]
    current_task_index: int
    
    # Using a serializable representation for VFS. 
    # In a real heavy production, we might store just a reference/ID, 
    # but here we'll store the files dict directly.
    vfs_data: Dict[str, Dict] # Filename -> File dict representation
    
    logs: Annotated[List[str], operator.add]
