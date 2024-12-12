import asyncio
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import logging
from Qdrant_Handler.local_VDB import search_relevant, save_text_to_qdrant
from Summary_Handler.local_translatorAgent import Local_TranslationAgent
from Summary_Handler.common_prompt import PromptGenerator
import re

class LLAMA:
    def __init__(self):
        self.model_name = "meta-llama/Llama-3.2-1B"
        # Eszköz explicit beállítása CPU-ra
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu") 
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()
        self.translator_agent = Local_TranslationAgent()
        self.promptGenerator = PromptGenerator()

############################################################################
# Create Summary
############################################################################
    async def summarize_documents_with_llama(self, combined_text: dict[str, str], sum_style:str, collection_name:str) -> str:
        summary_start = "Summary:"
        prompt_complex = self.promptGenerator.create_long_summary_prompt_en(sum_style)
        prompt_simple = self.promptGenerator.create_short_summary_prompt_en(sum_style)

        all_text = "\n".join([f"{filename}:\n{content}" for filename, content in combined_text.items()])
        max_tokens = 512
        subchunk_max_tokens = 256

        logging.debug(f"Combined text before splitting: {all_text[:500]}...")

        # Elsődleges chunk-okra bontás
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

        logging.debug(f"Total primary chunks created: {len(chunks)}")

        # Alchunk-okra bontás az egyes chunk-okban
        final_chunks = []
        for chunk in chunks:
            sentences = chunk.split(". ")
            current_subchunk = []
            current_subchunk_length = 0

            for sentence in sentences:
                tokenized_sentence = self.tokenizer(sentence, return_tensors="pt").input_ids.shape[1]
                if current_subchunk_length + tokenized_sentence > subchunk_max_tokens:
                    final_chunks.append(". ".join(current_subchunk))
                    current_subchunk = [sentence]
                    current_subchunk_length = tokenized_sentence
                else:
                    current_subchunk.append(sentence)
                    current_subchunk_length += tokenized_sentence

            if current_subchunk:
                final_chunks.append(". ".join(current_subchunk))

        logging.debug(f"Total final subchunks created: {len(final_chunks)}")

        ###########LITTLE############
        summaries = []
        for index, chunk in enumerate(final_chunks):
            prompt = f"Please summarize the following text in a concise and clear manner. Avoid repeating information.\n{chunk}\nSummary:"
            logging.debug(f"Chunk {index + 1} prompt: {prompt[:300]}...")

            input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids.to(self.device)

            if self.tokenizer.pad_token_id is None:
                self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

            with torch.no_grad():
                output = self.model.generate(
                    input_ids=input_ids,
                    attention_mask=torch.ones_like(input_ids).to(self.device),
                    max_new_tokens=150,
                    do_sample=True,
                    temperature=0.7,
                    repetition_penalty=1.2,
                    pad_token_id=self.tokenizer.pad_token_id
                )

            print("################# Kis összefoglalás ####################")
            summary_full = self.tokenizer.decode(output[0], skip_special_tokens=True).strip()
            if summary_start in summary_full:
                summary = summary_full[summary_full.index(summary_start) + len(summary_start):].strip()
            else:
                summary = summary_full
            print(summary)
            logging.debug(f"Generated summary for chunk {index + 1}: {summary}")
            summaries.append(summary)
            
        final_summary = "\n".join(summaries)
        final_prompt = (f"{prompt_complex} \n{final_summary}")
        logging.debug(f"Final prompt: {final_prompt[:300]}...")

        final_input_ids = self.tokenizer(final_prompt, return_tensors="pt").input_ids.to(self.device)

        with torch.no_grad():
            final_output = self.model.generate(
                input_ids=final_input_ids,
                attention_mask=torch.ones_like(final_input_ids).to(self.device),
                max_new_tokens=250,
                do_sample=True,
                temperature=0.7,
                repetition_penalty=1.2,
                pad_token_id=self.tokenizer.pad_token_id
            )
        print("################# Átfogó összefoglalás ####################")
        final_summary_text_full = self.tokenizer.decode(final_output[0], skip_special_tokens=True).strip()
        if summary_start in final_summary_text_full:
            final_summary_text = final_summary_text_full[final_summary_text_full.index(summary_start) + len(summary_start):].strip()
        else:
            final_summary_text = final_summary_text_full

        logging.debug(f"Final summary: {final_summary_text}")
        final_summary_text = self.remove_repeated_sentences(final_summary_text)
        save_text_to_qdrant(final_summary_text, "bot", collection_name)
        return final_summary_text
    
    def remove_repeated_sentences(self,text: str) -> str:
        sentences = text.split(". ")
        seen = set()
        unique_sentences = [sentence for sentence in sentences if sentence not in seen and not seen.add(sentence)]
        return ". ".join(unique_sentences)
############################################################################
# Question and answer
############################################################################
    async def generate_response(self, query: str, collection_name: str) -> str:
        summary_start = "CONTEXT:"
        try:
            
            query = self.translator_agent.instant_translate_to_english(query)

            relevant_texts = search_relevant(query, collection_name)
            if not relevant_texts:
                return "Sajnálom, de nem találtam releváns információt a kérdésedre."

            combined_text = " ".join(item["content"] for item in relevant_texts if "content" in item)

            prompt = (
                f"QUESTION:\n{query}\n"
                f"CONTEXT:\n{combined_text}\n"
                f"Answer the question in 1 concise sentence. Do not elaborate unnecessarily."
            )
            print(f"Generated prompt: {prompt}")

            input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids.to(self.device)
            if self.tokenizer.pad_token_id is None:
                self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

            with torch.no_grad():
                output = self.model.generate(
                    input_ids=input_ids,
                    attention_mask=torch.ones_like(input_ids).to(self.device),
                    max_new_tokens=20,
                    temperature=0.1,
                    do_sample=True,
                    top_p=0.9,
                    repetition_penalty=1.2,
                    pad_token_id=self.tokenizer.pad_token_id
                )

            response_full = self.tokenizer.decode(output[0], skip_special_tokens=True).strip()

            response_start = response_full.find(summary_start)
            if response_start != -1:
                response = response_full[response_start + len(summary_start):].strip()
            else:
                response = response_full

            print(f"Generated response: {response}")

            hungarian_answer = self.translator_agent.instant_translate_to_hungarian(response)
            return hungarian_answer

        except Exception as e:
            return f"Hiba történt a válasz generálása során: {str(e)}"
            

