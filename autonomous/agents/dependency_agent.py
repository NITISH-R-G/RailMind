import os
from autonomous.llm_client import LocalLLMClient

class DependencyAgent:
    def __init__(self):
        self.llm = LocalLLMClient()
        self.report_file = "docs/dependency_report.md"

    def run(self):
        print("Running Dependency Agent...")

        req_content = ""
        try:
            with open("backend/requirements.txt", "r") as f:
                req_content = f.read()
        except Exception:
            pass

        prompt = f"""
        You are a Dependency Analysis Agent.
        Review the following Python requirements:

        {req_content}

        Identify any potentially outdated or risky dependencies for an autonomous multi-agent system.
        Suggest modern alternatives or pinning strategies. Output in Markdown.
        """

        report = self.llm.generate(prompt)

        if report:
            os.makedirs(os.path.dirname(self.report_file), exist_ok=True)
            with open(self.report_file, "w") as f:
                f.write("# Dependency Analysis\n\n")
                f.write(report)
            print(f"Dependency report saved to {self.report_file}")

if __name__ == "__main__":
    agent = DependencyAgent()
    agent.run()
