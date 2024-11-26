import asyncio
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import logging
from Qdrant_Handler.local_VDB import search_relevant
from Summary_Handler.local_translatorAgent import Local_TranslationAgent
import re

class LLAMA:
    def __init__(self):
        self.model_name = "meta-llama/Llama-3.2-1B"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()
        self.translator_agent = Local_TranslationAgent()

    async def generate_response(self, query: str, prompt_style: str = "short", max_length: int = 250, temperature: float = 0.7, top_k: int = 5) -> str:
        query = self.translator_agent.translateLocal(query)

        relevant_texts = search_relevant(query, "documents_01")

        combined_text = await self.summarize_documents_with_llama(relevant_texts, sum_style="short")

        if not combined_text:
            return "Nincs releváns információ a kérdés megválaszolásához."

        prompt = self.prepare_prompt(query, combined_text, prompt_style)

        input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids.to(self.device)


        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        with torch.no_grad():
            output = self.model.generate(
                input_ids=input_ids,
                attention_mask=torch.ones_like(input_ids),
                max_new_tokens=150,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                pad_token_id=self.tokenizer.pad_token_id
            )

        answer = self.tokenizer.decode(output[0], skip_special_tokens=True)
        extracted_answer = self.extract_answer(answer, query)
        extracted_answer = self.translator_agent.translateLocal(extracted_answer)
        return extracted_answer

    def extract_answer(self, text: str, question: str) -> str:
        print(f"###Kérdés###: {question}")
        print(f"###Válasz###: {text}")

        pattern = re.compile(rf"{re.escape(question)}\s*(.*?)(?=Question:|$)", re.DOTALL)
        match = pattern.search(text)

        if match:
            answer = match.group(1).strip()
            if answer.startswith("Answer:"):
                answer = answer[len("Answer:"):].strip()
            return answer
        else:
            return "Nincs megtalálható válasz a kérdésre."
        
    async def summarize_documents_with_llama(self, combined_text: dict[str, str], sum_style: str = "short") -> str:
        all_text = "\n".join([f"{filename}:\n{content}" for filename, content in combined_text.items()])
        max_tokens = 512

        logging.debug(f"Combined text before splitting: {all_text[:500]}...")

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in all_text.split(". "):
            tokenized_sentence = self.tokenizer(sentence, return_tensors="pt").input_ids.shape[1]
            if current_length + tokenized_sentence > max_tokens:
                chunks.append(". ".join(current_chunk))
                current_chunk = [sentence]
                current_length = tokenized_sentence
            else:
                current_chunk.append(sentence)
                current_length += tokenized_sentence

        if current_chunk:
            chunks.append(". ".join(current_chunk))

        logging.debug(f"Total chunks created: {len(chunks)}")

        summaries = []
        for index, chunk in enumerate(chunks):
            prompt = (
                f"Provide a factual summary of the following text. Do not include any additional information or assumptions. "
                f"Only use the information provided in the text:\n{chunk}\nSummary:"
            )
            logging.debug(f"Chunk {index + 1} prompt: {prompt[:300]}...")

            input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids.to(self.device)

            if self.tokenizer.pad_token_id is None:
                self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

            with torch.no_grad():
                output = self.model.generate(
                    input_ids=input_ids,
                    attention_mask=torch.ones_like(input_ids),
                    max_new_tokens=150,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id
                )

            summary = self.tokenizer.decode(output[0], skip_special_tokens=True)
            logging.debug(f"Generated summary for chunk {index + 1}: {summary}")
            summaries.append(summary)

        final_summary = "\n".join(summaries)
        final_prompt = (
            f"Create a concise and factual summary of the following text, using only the provided information. "
            f"Do not add any new information or interpretations:\n{final_summary}\nFinal Summary:"
        )
        logging.debug(f"Final prompt: {final_prompt[:300]}...")

        final_input_ids = self.tokenizer(final_prompt, return_tensors="pt").input_ids.to(self.device)

        with torch.no_grad():
            final_output = self.model.generate(
                input_ids=final_input_ids,
                attention_mask=torch.ones_like(final_input_ids),
                max_new_tokens=250,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id
            )

        final_summary_text = self.tokenizer.decode(final_output[0], skip_special_tokens=True)
        logging.debug(f"Final summary: {final_summary_text}")
        print("############## NÉZD MEG ###################")
        print(final_summary_text)
        final_summary_text = self.extract_summary(final_summary_text)

        return final_summary_text
    
    def extract_summary(self, text: str) -> str:

        pattern = re.compile(r"Final Summary:\s*(.*)", re.DOTALL)
        match = pattern.search(text)

        if match:
            summary = match.group(1).strip()
            return summary
        else:
            return "Nincs megtalálható összefoglaló."