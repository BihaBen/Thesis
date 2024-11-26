import openai
import os
import asyncio
import logging
import tiktoken
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from Qdrant_Handler.global_VDB import search_relevant, store_respond
from Summary_Handler.common_prompt import create_summary_prompt
import asyncio

load_dotenv()

class GPT4:
    def __init__(self):
        """
        Inicializálja a GPT4Summarizer osztályt a megadott modellnévvel.
        
        :param model: Az OpenAI modell neve, például "gpt-4o".
        """
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4o"
        self.max_model_tokens = 32768

    def get_prompt_token_count(self, prompt):
        tokenizer = tiktoken.encoding_for_model(self.model)
        return len(tokenizer.encode(prompt))



    async def call_openai_api(self, prompt: str, chunk: str, max_tokens: int, temperature: float, max_retries: int = 5) -> str:
        retry_count = 0

        while retry_count < max_retries:
            try:
                response = await asyncio.to_thread(
                    openai.ChatCompletion.create,
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert assistant summarizing complex documents."},
                        {"role": "user", "content": prompt + chunk}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response['choices'][0]['message']['content']

            except openai.error.RateLimitError as e:
                wait_time = float(str(e).split("try again in")[1].split("s")[0].strip())
                print(f"Rate limit elérve, várakozás {wait_time} másodpercig...")
                await asyncio.sleep(wait_time)
                retry_count += 1

            except Exception as e:
                print(f"Hiba történt az OpenAI API hívás során: {e}")
                break

        print("Az újrapróbálkozások száma elérte a maximumot.")
        return ""


    async def process_document(self, doc_name: str, doc_content: str, prompt_complex: str, max_token_numb: int) -> str:
        chunks = [doc_content[i:i + max_token_numb] for i in range(0, len(doc_content), max_token_numb)]
        part_of_summary = ""

        tasks = [self.call_openai_api(prompt_complex, chunk, 2048, 0.7) for chunk in chunks]
        results = await asyncio.gather(*tasks)

        for partial_summary in results:
            part_of_summary += partial_summary + "\n"

        return part_of_summary

    async def generate_summary(self, documents: dict[str, str], sum_style: str, collection_name: str) -> str:
        try:
            summary = ""
            prompt_complex = create_summary_prompt(sum_style, "")
            prompt_simple = create_summary_prompt("short", "")
            prompt_token_count = self.get_prompt_token_count(prompt_complex)

            max_token_numb = self.max_model_tokens - prompt_token_count - 500

            tasks = [
                self.process_document(doc_name, doc_content, prompt_complex, max_token_numb)
                for doc_name, doc_content in documents.items()
            ]

            summaries = await asyncio.gather(*tasks)

            for doc_name, part_of_summary in zip(documents.keys(), summaries):
                response = await self.call_openai_api(prompt_simple, part_of_summary, 2048, 0.2)
                summary += response + "\n"

            summary_dict = {"summary": summary}
            store_respond(summary_dict, collection_name)

            total_token_count = self.get_prompt_token_count(summary)
            print(f"Az össz token szám: {total_token_count}")

            return summary
        except Exception as e:
            logging.error(f"Hiba történt a dokumentum összefoglalás során: {e}")
            return ""

    async def summarize_chunk(self, chunk, prompt):
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert assistant summarizing complex documents."},
                {"role": "user", "content": prompt + chunk}
            ],
            max_tokens=2048,
            temperature=0.7,
            stream=True
        )
        summary = ""
        async for message in response:
            if "content" in message["choices"][0]["delta"]:
                summary += message["choices"][0]["delta"]["content"]

        return summary

    def count_tokens(self, text):
        tokenizer = tiktoken.encoding_for_model(self.model)
        return len(tokenizer.encode(text))

    def split_text_by_tokens(self, text, max_tokens, overlap=200):
        tokenizer = tiktoken.encoding_for_model(self.model)
        tokens = tokenizer.encode(text)
        chunks = []
        start = 0
        while start < len(tokens):
            end = min(start + max_tokens, len(tokens))
            chunk = tokenizer.decode(tokens[start:end])
            chunks.append(chunk)
            start = end - overlap
        return chunks

    def generate_gpt4_response(self, query: str) -> str:
        try:
            relevant_chunks = search_relevant(query, "documents_01")

            if not relevant_chunks:
                return "Nem találtam releváns információt a kérdésedhez."

            context = "\n".join([f"- {chunk['content']}" for chunk in relevant_chunks])
            input_text = f"A kérdés: {query}\nA következő kontextus alapján válaszolj:\n{context}\nVálasz:"

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": input_text}
                ],
                max_tokens=1500,
                temperature=0.7
            )

            answer = response['choices'][0]['message']['content'].strip()

            return answer

        except Exception as e:
            logging.error(f"Hiba történt a GPT-4 válasz generálása során: {str(e)}")
            return "Hiba történt a válasz generálása során."

