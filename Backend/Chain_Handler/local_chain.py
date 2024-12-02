from langchain.chains.base import Chain  # Alap láncosztály a helyőrzőkhöz
from fastapi import  HTTPException
from typing import Dict
from langchain.chains import SequentialChain
from Milestone_Handler.common_milestone import update_milestone
###########################################################################
# Loading files and extracting their contents
###########################################################################
import os
from Files_Handler.common_load_file import process_files_in_directory
collection_name="documents_01"

class LoadFilesChain(Chain):
    def _call(self, inputs: Dict) -> Dict:
        file_path = inputs.get("file_path", "")

        print(f"LoadFilesChain: Fájlok feldolgozása megkezdődött. Könyvtár: {file_path}")

        try:
            dict_dataOfEachFile = process_files_in_directory(file_path)
            self.Show_Result(dict_dataOfEachFile)

            return {"combined_text": dict_dataOfEachFile}
            
        except Exception as e:
            print(f"LoadFilesChain Error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error in LoadFilesChain: {str(e)}")
    
    def Show_Result(self, dict_dataOfEachFile:Dict)-> None:
        print("LoadFilesChain: Fájlok sikeresen feldolgozva.")
        print("\n=== Feldolgozott fájlok tartalma ===")
        for filename, content in dict_dataOfEachFile.items():
            print(f"Fájl: {filename}")
            print(f"Tartalom:\n{content}\n")
            print("====================================\n")
            update_milestone(2, True)

    @property
    def input_keys(self) -> list:
        return ["file_path", "stored_data"]

    @property
    def output_keys(self) -> list:
        return ["combined_text"]

###########################################################################
# Vector Database storage
###########################################################################
from pydantic import BaseModel, Field
from langchain.chains.base import Chain
from Qdrant_Handler.local_VDB import initialize_qdrant, process_document

class VectorStoreChain(Chain, BaseModel):
    vector_size: int = Field(...)

    def _call(self, inputs: Dict) -> Dict:
        combined_text = inputs["combined_text"]

        initialize_qdrant(collection_name, self.vector_size)

        qdrantVectorbase = process_document(combined_text, collection_name)

        self.Show_Result()

        return {"qdrant_vectorbase": qdrantVectorbase}
    
    def Show_Result(self)-> None:
        print(f"VectorStoreChain: A fájlok sikeresen eltárolva a {collection_name} vektoradatbázisba.")
        update_milestone(3, True)
    @property
    def input_keys(self):
        return ["combined_text"]

    @property
    def output_keys(self):
        return ["qdrant_vectorbase"]

###########################################################################
# Text analysis
###########################################################################
from Summary_Handler.common_contentExtraction import generate_extract_from_texts

class AnalyzeProcessChain(Chain):
    def _call(self, inputs: Dict) -> Dict:
        dict_dataOfEachFile = inputs.get("combined_text", "")
        
        try:
            combined_text = "\n".join(dict_dataOfEachFile.values())
            print("AnalyzeProcessChain: Tartalom elemzése megkezdődött.")

            analysis_result = generate_extract_from_texts(combined_text)
            
            self.Show_Result(analysis_result)

            return {"analysis_result": analysis_result}
        
        except Exception as e:
            print(f"AnalyzeProcessChain Error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error in AnalyzeProcessChain: {str(e)}")

    def Show_Result(self, analysis_result:str)-> None:
        print(f"A szöveg analizálás ilyen tartalommal végződött:\n{analysis_result}")
        update_milestone(4, True)

    @property
    def input_keys(self) -> list:
        return ["combined_text"]

    @property
    def output_keys(self) -> list:
        return ["analysis_result"]
    
###########################################################################
# Content summary
###########################################################################
from langchain.chains.base import Chain
from Models_Handler.local_model import LLAMA
import asyncio

class SummarizeContentChain(Chain):
    def _call(self, inputs: Dict) -> Dict:
        stored_data = inputs.get("stored_data", {})
        combined_text = inputs["combined_text"]

        try:
            chatbotStyle = stored_data.get("chatbotStyle", "clear")
            print("SummarizeContentChain: Az elemzett tartalom összefoglalása megkezdődött.")
            llama_model = LLAMA()

            summary_result = asyncio.run(llama_model.summarize_documents_with_llama(combined_text,chatbotStyle,collection_name))
            
            self.Show_Result(summary_result)
            
            return {"summary_result": summary_result}
        
        except Exception as e:
            print(f"SummarizeContentChain Error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error in SummarizeContentChain: {str(e)}")

    def Show_Result(self, summary_result:str) -> None:
        print(f"Összefoglaló:\n{summary_result}")
        update_milestone(5, True)
        update_milestone(6, True)

    @property
    def input_keys(self) -> list:
        return ["analysis_result"]

    @property
    def output_keys(self) -> list:
        return ["summary_result"]

###########################################################################
# Translate
###########################################################################
from Summary_Handler.local_translatorAgent import Local_TranslationAgent


class TranslateContentChain(Chain):
    def _call(self, inputs: Dict) -> Dict:
        summary_result = inputs["summary_result"]
        analysis_result = inputs["analysis_result"]
        translator_agent = Local_TranslationAgent()

        try:
            str_essence = summary_result
            print(str_essence)
            hungarian_summary = translator_agent.instant_translate_to_hungarian(str_essence)
            print(f"Magyarul:\n{str_essence}")
            hungarian_summary += "\n\n" + analysis_result
            self.Show_Result(hungarian_summary)
            final_summary = hungarian_summary

            return {"final_summary": final_summary}
        
        except Exception as e:
            print(f"SummarizeContentChain Error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error in SummarizeContentChain: {str(e)}")

    def Show_Result(self, hungarian_summary: str) -> None:
        print(f"Összefoglaló:\n{hungarian_summary}")
        update_milestone(7, True)

    @property
    def input_keys(self) -> list:
        return ["analysis_result"]

    @property
    def output_keys(self) -> list:
        return ["final_summary"]

###########################################################################
# Initialize chains
###########################################################################
load_files_chain = LoadFilesChain()
vector_store_chain = VectorStoreChain(vector_size=512)
analyze_process_chain = AnalyzeProcessChain()
summarize_content_chain = SummarizeContentChain()
translate_content_chain = TranslateContentChain()
###########################################################################
# Create the localSummarizer_chain using SequentialChain
###########################################################################
local_summarizer_chain = SequentialChain(
    chains=[load_files_chain, vector_store_chain, analyze_process_chain, summarize_content_chain, translate_content_chain],
    input_variables=["file_path", "stored_data"],
    output_variables=["final_summary"]
)

