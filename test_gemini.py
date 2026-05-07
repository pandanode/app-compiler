from pipeline.repair import call_llm

result = call_llm(
    system_prompt="You are a helpful assistant. Return only valid JSON.",
    user_message='Return this exact JSON: {"status": "working", "model": "gemini"}'
)
print("Gemini response:")
print(result)
