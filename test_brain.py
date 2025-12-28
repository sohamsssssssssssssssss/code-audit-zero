from shared.llm_core import ask_llm

print("🧠 Testing the Brain...")
response = ask_llm("You are a poet.", "Write a haiku about a security robot.")
print(f"\nRESULT:\n{response}")