import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from config import Config

class LLMWrapper:
    def __init__(self):
        print(f"Loading LLM: {Config.MODEL_ID}...")
        self.tokenizer = AutoTokenizer.from_pretrained(Config.MODEL_ID)
        
        # Tự động chọn thiết bị (GPU nếu có, CPU nếu không)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.model = AutoModelForCausalLM.from_pretrained(
            Config.MODEL_ID,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None
        )
        if device == "cpu":
            self.model.to("cpu")
            
        print("LLM Loaded successfully.")

    def generate(self, prompt, max_new_tokens=512):
        messages = [
            {"role": "system", "content": "Bạn là nhân viên hỗ trợ đặt món tại nhà hàng Hòa Viên."},
            {"role": "user", "content": prompt}
        ]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=max_new_tokens,
            pad_token_id=self.tokenizer.eos_token_id
        )
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        return self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]