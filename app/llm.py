#%%
import torch
import time
from transformers import AutoTokenizer, AutoModelForCausalLM
import os

#%%
# Define function that prompts the model 
def prompt_model(prompt, model_name, hf_access_token, max_length=1024, device=None):
   
    # Set device on which you'll run the model 
    if not device:
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf", token=hf_access_token, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_name, token=hf_access_token, trust_remote_code=True)
    model.to(device).eval()
    print('yay')

    # Encode prompt
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(device)
    print('nay')

    # Generate and time the process
    start_time = time.time()
    outputs = model.generate(inputs["input_ids"], max_length=max_length)
    generation_time = time.time() - start_time
    print('yyyyyyyyy')
    print(generation_time)
    # Decode and print output
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"Generated in {generation_time:.2f} seconds: {generated_text}")


#%%
model_name = "apple/OpenELM-3B-Instruct"
# Give your Hugging Face Token
# hf_access_token = os.environ('hf_token')
# hf_access_token = os.environ(hf_access_token)
# Define Prompt
prompt = "\nName all the countries in the world, list of current vs historical"
print(prompt)
print(hf_access_token)
# Prompt the model
prompt_model(prompt, model_name, hf_access_token)
# %%
