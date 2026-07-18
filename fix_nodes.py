import re

with open('backend/agents/nodes.py', 'r') as f:
    content = f.read()

if "import time" not in content[:500]:
    content = content.replace("from datetime import datetime", "from datetime import datetime\nimport time")
else:
    # time is already imported at the top, check if it's imported inside reason_node
    content = content.replace("import time\n        import json", "import json")

with open('backend/agents/nodes.py', 'w') as f:
    f.write(content)
