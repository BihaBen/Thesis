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
        self.device = "cpu"  
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
        max_tokens = 512  # Chunkok maximális hossza tokenekben
        subchunk_max_tokens = 256  # Alchunkok maximális hossza

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
            prompt = (f"Please summarize the following text in a concise and clear manner:\n{chunk}\nSummary:")
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
                    pad_token_id=self.tokenizer.pad_token_id
                )

            print("################# NEW ####################")
            summary_full = self.tokenizer.decode(output[0], skip_special_tokens=True).strip()
            if summary_start in summary_full:
                summary = summary_full[summary_full.index(summary_start) + len(summary_start):].strip()
            else:
                summary = summary_full
            print(summary)
            logging.debug(f"Generated summary for chunk {index + 1}: {summary}")
            summaries.append(summary)
        summ="\n".join(summaries)
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
                pad_token_id=self.tokenizer.pad_token_id
            )
        print("################# FINAL ####################")
        final_summary_text_full = self.tokenizer.decode(final_output[0], skip_special_tokens=True).strip()
        if summary_start in final_summary_text_full:
            final_summary_text = final_summary_text_full[final_summary_text_full.index(summary_start) + len(summary_start):].strip()
        else:
            final_summary_text = final_summary_text_full

        logging.debug(f"Final summary: {final_summary_text}")
        print("############## NÉZD MEG ###################")
        print(final_summary_text)

        save_text_to_qdrant(final_summary_text, "bot", collection_name)
        return summ
    
############################################################################
# Question and answer
############################################################################
    async def generate_response(self, query: str, collection_name: str) -> str:
        summary_start = "CONTEXT:"
        try:
            # Fordítás angolra
            query = self.translator_agent.instant_translate_to_english(query)

            # 1. Releváns szövegek lekérése
            relevant_texts = search_relevant(query, collection_name)
            if not relevant_texts:
                return "Sajnálom, de nem találtam releváns információt a kérdésedre."

            # 2. Szövegek egyesítése
            combined_text = " ".join(item["content"] for item in relevant_texts if "content" in item)

            # 3. Prompt előkészítése
            prompt = (
                f"QUESTION:\n{query}\n"
                f"CONTEXT:\n{combined_text}\n"
                f"Answer the question in maximum 1 sentence. Be concise."
            )
            print(f"Generated prompt: {prompt}")

            # 4. Tokenizálás
            input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids.to(self.device)
            if self.tokenizer.pad_token_id is None:
                self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

            # 5. Modell válasz generálása
            with torch.no_grad():
                output = self.model.generate(
                    input_ids=input_ids,
                    attention_mask=torch.ones_like(input_ids).to(self.device),
                    max_new_tokens=50,  # Limitáld a válasz maximális hosszát
                    temperature=0.1,  # Csökkentsd a kreativitást a precíz válasz érdekében
                    do_sample=False,  # Használj determinisztikus generálást
                    top_p=0.8,  # Szűkítsd a lehetséges kimeneteket
                    pad_token_id=self.tokenizer.pad_token_id
                )

            # 6. A válasz dekódolása
            response_full = self.tokenizer.decode(output[0], skip_special_tokens=True).strip()

            # Csak a válasz releváns részét ragadjuk meg
            response_start = response_full.find(summary_start)
            if response_start != -1:
                response = response_full[response_start + len(summary_start):].strip()
            else:
                response = response_full

            print(f"Generated response: {response}")

            # 7. Fordítás magyarra
            hungarian_answer = self.translator_agent.instant_translate_to_hungarian(response)
            return hungarian_answer

        except Exception as e:
            return f"Hiba történt a válasz generálása során: {str(e)}"
            
    def extract_answer(self, text: str, question: str) -> str:
        """
        Extract the answer from the generated text based on the original question.
        """
        try:
            print(f"### Kérdés ###: {question}")
            print(f"### Válasz ###: {text}")

            # Regex a válasz kinyeréséhez
            pattern = re.compile(rf"{re.escape(question)}\s*(.*?)(?=Question:|$)", re.DOTALL)
            match = pattern.search(text)

            if match:
                answer = match.group(1).strip()
                if answer.startswith("Answer:"):
                    answer = answer[len("Answer:"):].strip()
                return answer
            else:
                return "Nem található válasz a kérdésre."
        except Exception as e:
            print(f"Error in extracting answer: {str(e)}")
            return "Nem található válasz a kérdésre."

