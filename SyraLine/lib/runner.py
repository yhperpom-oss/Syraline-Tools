"""Run a tool inside the common terminal interface."""
from .entry import run_syraline

def run_tool(tool_id,language):
    run_syraline(['--tool',tool_id,'--lang',language])
