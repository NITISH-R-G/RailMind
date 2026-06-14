import re

with open("backend/agents/state.py", "r") as f:
    content = f.read()

# Define the custom reducer that properly handles clears (like append_to_list already does)
custom_reducer_code = """
def custom_reducer(a: Optional[List], b: Optional[List]) -> List:
    if a is None:
        a = []
    if b is None:
        b = []

    # Handle specific CLEAR token to empty the list
    if b and b[0] == "CLEAR":
        return []

    return a + b
"""

# add after append_to_list if custom_reducer doesn't exist
if "def custom_reducer" not in content:
    content = content.replace("def append_to_list", custom_reducer_code + "\ndef append_to_list")

# Now update operator.add to custom_reducer where appropriate to prevent list duplicates when returning differentials
content = content.replace("Annotated[List[DepartmentTask], operator.add]", "Annotated[List[DepartmentTask], custom_reducer]")
content = content.replace("Annotated[list, operator.add]", "Annotated[list, custom_reducer]")
content = content.replace("Annotated[List[TrainAnomaly], append_to_list]", "Annotated[List[TrainAnomaly], custom_reducer]")
content = content.replace("Annotated[List[str], append_to_list]", "Annotated[List[str], custom_reducer]")

with open("backend/agents/state.py", "w") as f:
    f.write(content)
