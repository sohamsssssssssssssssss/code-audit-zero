from shared.llm_core import ask_llm_text

print("🧠 Testing the Brain...")
response = ask_llm_text("You are a poet.", "Write a haiku about a security robot.")
print(f"\nRESULT:\n{response}")