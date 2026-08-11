import sys
import re

def fix_gemini():
    with open('backend/agents/nodes.py', 'r') as f:
        content = f.read()

    # The actual AI call inside `reason_node` uses `call_gemini` directly without circuit breaker.
    # And we need to use the `ai_circuit_breaker`.

    old_gemini_def = """async def call_gemini(prompt: str, state: AgentState = None) -> dict:"""

    # We will rename the original to _call_gemini_internal, and wrap it
    new_gemini_def = """async def _call_gemini_internal(prompt: str, state: AgentState = None) -> dict:"""
    content = content.replace(old_gemini_def, new_gemini_def)

    # Inject the wrapped call_gemini
    wrapper = """async def call_gemini(prompt: str, state: AgentState = None) -> dict:
    async def _call_ai():
        res = await _call_gemini_internal(prompt, state)
        TOKEN_CONSUMPTION.labels(agent_name='gemini_claude').inc(100)
        return res

    async def _fallback_ai():
        TOKEN_CONSUMPTION.labels(agent_name='local_fallback').inc(50)
        return get_local_llm_fallback()

    return await execute_with_circuit_breaker(ai_circuit_breaker, _call_ai, _fallback_ai)

async def _call_gemini_internal(prompt: str, state: AgentState = None) -> dict:"""

    content = content.replace(new_gemini_def, wrapper)

    with open('backend/agents/nodes.py', 'w') as f:
        f.write(content)

if __name__ == "__main__":
    fix_gemini()
