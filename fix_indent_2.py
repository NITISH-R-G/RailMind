import re
with open("backend/agents/nodes.py", "r") as f:
    content = f.read()

# Fix the specific indentation error at line 1434
# It was likely inside `except Exception as e:` in `supervisor_node`
supervisor_except_block = """    except Exception as e:
         import traceback
        logger.exception("Error in supervisor_node")
        tb = traceback.format_exc()
        await log_agent("supervisor_node", f"[RAILMIND] [ERROR] Supervisor node failed: {e}\\n{tb}")
        return {"next_node": "END", "last_node_executed": "supervisor_node"}"""

fixed_except_block = """    except Exception as e:
        import traceback
        logger.exception("Error in supervisor_node")
        tb = traceback.format_exc()
        await log_agent("supervisor_node", f"[RAILMIND] [ERROR] Supervisor node failed: {e}\\n{tb}")
        return {"next_node": "END", "last_node_executed": "supervisor_node"}"""

content = content.replace(supervisor_except_block, fixed_except_block)

with open("backend/agents/nodes.py", "w") as f:
    f.write(content)
