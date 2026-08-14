def replace_nodes():
    with open('backend/agents/nodes.py', 'r') as f:
        content = f.read()

    # Find the start of call_gemini
    import re

    start_str = 'async def call_gemini(prompt: str, state: AgentState = None) -> dict:'

    # We will replace everything from start_str to the line before `async def execute_tool`
    end_str = 'async def execute_tool(tool_name: str, params: dict, reason: str, state: AgentState):'

    start_idx = content.find(start_str)
    end_idx = content.find(end_str)

    if start_idx == -1 or end_idx == -1:
        print("Could not find start or end of call_gemini")
        return

    replacement = """def extract_json_from_text(response_text: str) -> dict:
    clean_text = response_text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    clean_text = clean_text.strip()
    return json.loads(clean_text)

async def call_ollama_fallback(prompt: str) -> str:
    import httpx
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            settings.OLLAMA_BASE_URL,
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt + "\\n\\nRespond ONLY with a valid JSON block matching the requested format.",
                "stream": False,
                "format": "json"
            }
        )
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("response", "")

async def call_gemini_api(prompt: str, gemini_key: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = await model.generate_content_async(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    response_text = response.text
    agent_tokens_consumed.inc(model.count_tokens(prompt).total_tokens + model.count_tokens(response_text).total_tokens)
    return response_text

async def call_claude_api(prompt: str, anthropic_key: str) -> str:
    from anthropic import AsyncAnthropic
    client = AsyncAnthropic(api_key=anthropic_key)
    response = await client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        system="You must respond ONLY with a valid JSON block matching the requested format.",
        messages=[{"role": "user", "content": prompt}]
    )
    response_text = response.content[0].text
    agent_tokens_consumed.inc(response.usage.input_tokens + response.usage.output_tokens)
    return response_text

async def call_gemini(prompt: str, state: AgentState = None) -> dict:
    if not llm_circuit_breaker.can_execute():
        logger.warning("LLM Circuit Breaker is OPEN. Shifting to local LLM via Ollama.")
        try:
            response_text = await call_ollama_fallback(prompt)
            if response_text:
                return extract_json_from_text(response_text)
        except Exception as e:
            logger.warning(f"Local LLM fallback failed: {e}. Using mock fallback.")
        return generate_mock_json_fallback(prompt, state)

    gemini_key = settings.GEMINI_API_KEY
    anthropic_key = settings.ANTHROPIC_API_KEY

    response_text = None

    if gemini_key and gemini_key != "mock_key":
        try:
            response_text = await call_gemini_api(prompt, gemini_key)
            llm_circuit_breaker.record_success()
        except Exception as e:
            logger.warning(f"Gemini API call failed: {e}. Trying fallback.")

    if not response_text and anthropic_key and anthropic_key != "mock_key":
        try:
            response_text = await call_claude_api(prompt, anthropic_key)
            llm_circuit_breaker.record_success()
        except Exception as e:
            logger.warning(f"Claude fallback API call failed: {e}. Using mock fallback.")

    if not response_text:
        llm_circuit_breaker.record_failure()
        return generate_mock_json_fallback(prompt, state)

    try:
        return extract_json_from_text(response_text)
    except Exception as e:
        logger.warning(f"Failed to parse LLM response as JSON: {e}")
        return generate_mock_json_fallback(prompt, state)

"""

    new_content = content[:start_idx] + replacement + content[end_idx:]
    with open('backend/agents/nodes.py', 'w') as f:
        f.write(new_content)
    print("Done")

replace_nodes()
