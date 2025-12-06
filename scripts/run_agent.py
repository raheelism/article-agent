import argparse
import asyncio
from app.main_graph import create_main_graph
from app.core.vfs import VFS

def main():
    parser = argparse.ArgumentParser(description="Run the Article Agent")
    parser.add_argument("topic", help="Topic to write about")
    parser.add_argument("--word-count", type=int, default=1500)
    args = parser.parse_args()
    
    # Initialize State
    initial_state = {
        "topic": args.topic,
        "word_count": args.word_count,
        "language": "English",
        "plan": [],
        "current_task_index": 0,
        "vfs_data": {}, # Empty VFS
        "logs": []
    }
    
    print(f"Starting Agent for topic: {args.topic}")
    
    graph = create_main_graph()
    
    # Run the graph
    # Using .invoke (synchronous wrapper for convenience, or async via ainvoke)
    # LangGraph .invoke returns the final state
    final_state = graph.invoke(initial_state)
    
    print("\n--- Execution Complete ---")
    
    # Extract the draft
    vfs_files = final_state.get("vfs_data", {})
    if "draft.md" in vfs_files:
        print("\n--- Final Draft ---")
        # In the state, vfs_data is a dict of filename -> File object (Wait, Pydantic objects or dicts?)
        # Let's check how we stored it. In vfs.py, we have `_files: Dict[str, File]`.
        # When we do `vfs._files = ...` in the nodes, we are passing the internal dict.
        # LangGraph might serialize Pydantic objects if configured, or we might see dicts.
        
        draft_obj = vfs_files["draft.md"]
        # If it's a Pydantic object
        if hasattr(draft_obj, "content"):
            print(draft_obj.content)
            # Save to disk for inspection
            with open("final_article.md", "w") as f:
                f.write(draft_obj.content)
        else:
             # If it became a dict
             print(draft_obj.get("content"))
             with open("final_article.md", "w") as f:
                f.write(draft_obj.get("content"))
             
        print(f"\nSaved to final_article.md")
    else:
        print("No draft.md found in VFS.")

if __name__ == "__main__":
    main()
