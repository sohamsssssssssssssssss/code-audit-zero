import os
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import json

app = FastAPI(title="Code-Audit Zero Inference Server")

# Configuration
BASE_MODEL = "deepseek-ai/deepseek-coder-7b-base-v1.5"
ADAPTER_PATH = "/model/adapter"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
if torch.backends.mps.is_available():
    DEVICE = "mps"

print(f"Loading Base Model: {BASE_MODEL} on {DEVICE}...")

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.float16 if DEVICE != "cpu" else torch.float32,
    trust_remote_code=True,
    device_map="auto" if DEVICE != "cpu" else None,
    load_in_4bit=(DEVICE != "cpu" and DEVICE != "mps") # Use 4-bit for CUDA if available
)

print(f"Loading LoRA Adapter from: {ADAPTER_PATH}...")
model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
model.to(DEVICE)
model.eval()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    messages: list[ChatMessage]
    temperature: float = 0.1
    max_tokens: int = 1000

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    # Construct prompt in DeepSeek style
    prompt = ""
    for msg in request.messages:
        if msg.role == "system":
            prompt += f"### System Prompt\n{msg.content}\n\n"
        elif msg.role == "user":
            prompt += f"### Instruction\n{msg.content}\n\n"
        elif msg.role == "assistant":
            prompt += f"### Response\n{msg.content}\n\n"
    
    prompt += "### Response\n"

    inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            do_sample=request.temperature > 0,
            pad_token_id=tokenizer.eos_token_id
        )
    
    response_text = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": response_text
                }
            }
        ]
    }

@app.get("/health")
async def health():
    return {"status": "ok", "device": DEVICE, "model": BASE_MODEL}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
