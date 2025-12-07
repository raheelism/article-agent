import argparse
import asyncio
import os
import re
import sys
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main_graph import create_main_graph
from app.core.vfs import VFS


def sanitize_filename(topic: str) -> str:
    """Convert topic to a safe filename."""
    # Remove special characters and replace spaces with underscores
    filename = re.sub(r'[<>:"/\\|?*]', '', topic)
    filename = re.sub(r'\s+', '_', filename.strip())
    filename = filename[:50]  # Limit length
    return filename

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
            content = draft_obj.content
        else:
            # If it became a dict
            content = draft_obj.get("content", "")
        
        print(content)
        
        # Create output directory
        output_dir = "Generated articles"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename from topic
        safe_name = sanitize_filename(args.topic)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)
        
        # Save the article
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
             
        print(f"\nSaved to {filepath}")
    else:
        print("No draft.md found in VFS.")

if __name__ == "__main__":
    main()
