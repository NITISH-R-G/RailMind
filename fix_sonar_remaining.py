import re

with open("backend/agents/nodes.py", "r") as f:
    content = f.read()

# Fix "Catch this exception only once" at line ~538
# Look for consecutive except Exception as e blocks in predict_node.
predict_node_end = """        try:
            await websocket_manager.broadcast(json.dumps({
                "type": "PREDICTION_UPDATE",
                "data": prediction
            }))
        except Exception as e:
            logger.exception(ERR_BROADCAST_MSG, e)
    except Exception as e:
        logger.exception(ERR_OCCURRED_MSG, e)"""

fixed_predict_node_end = """        try:
            await websocket_manager.broadcast(json.dumps({
                "type": "PREDICTION_UPDATE",
                "data": prediction
            }))
        except OSError as e: # Changed generic Exception to specific to avoid shadowing
            logger.exception(ERR_BROADCAST_MSG, e)
    except Exception as e:
        logger.exception(ERR_OCCURRED_MSG, e)"""

content = content.replace(predict_node_end, fixed_predict_node_end)


with open("backend/agents/nodes.py", "w") as f:
    f.write(content)
