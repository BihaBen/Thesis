##########################################################################
# FASTAPI basic backend
##########################################################################
from fastapi import FastAPI
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
##########################################################################
# TEST: GET endpoints
##########################################################################
stored_data = {}

@app.get("/")
async def read_root():
    return {"Website ": "The website is running successfully!"}

@app.get("/api/metadata")
async def get_data():
    return {"data": stored_data}

@app.get("/status")
async def get_status():
    return {"message": "Sikeres csatlakozás!"}

##########################################################################
# Save all data from Frontend
##########################################################################
from fastapi import Form,UploadFile, File
from typing import List
import traceback

input_data={}

@app.post("/api/saveAllData")
async def save_alldata(
    isStoreInLocal: str = Form(...),
    chatbotStyle: str = Form(...),
    files: List[UploadFile] = File(...)
):
    global input_data
    try:
        stored_data = {
            "chatbotStyle": chatbotStyle,
            "isStoreInLocal": isStoreInLocal.lower() == "true",
        }

        temp_dir = "temp_files"
        os.makedirs(temp_dir, exist_ok=True)
        for file in files:
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as out_file:
                content = await file.read()
                out_file.write(content)
            print(f"Fájl lementve: {file_path}")

        input_data = {
            "file_path": temp_dir,
            "stored_data": stored_data
        }

        return {"message": "Metaadatok és fájlok elmentve"}
    except Exception as e:
        print("Hiba történt:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Hiba történt: {str(e)}")
    
##########################################################################
# Milestones
##########################################################################
from pydantic import BaseModel

class Milestone(BaseModel):
    id: int
    title: str
    completed: bool

milestones = [
    {"id": 1, "title": "Fájlok lekérése és metaadatok eltárolása", "completed": True},
    {"id": 2, "title": "Tartalom átalakítás", "completed": False},
    {"id": 3, "title": "Tárolás vektoradatbázisban", "completed": False},
    {"id": 4, "title": "Adatok analizálása", "completed": False},
    {"id": 5, "title": "Javaslatok meghozatala", "completed": False},
    {"id": 6, "title": "Összefoglalás generálása", "completed": False},
    {"id": 7, "title": "Üzenet formázása", "completed": False}
]

@app.get("/milestones", response_model=List[Milestone])
def get_milestones():
    return milestones

class UpdateMilestone(BaseModel):
    id: int
    completed: bool

@app.post("/update_milestone")
def update_milestone(update: UpdateMilestone):
    for milestone in milestones:
        if milestone["id"] == update.id:
            milestone["completed"] = update.completed
            return {"message": f"Mérföldkő frissítve: {milestone['title']}", "status": update.completed}
    return {"error": "Mérföldkő nem található"}

##########################################################################
# Generate summary
##########################################################################
from Chain_Handler.global_chain import global_summarizer_chain
from Chain_Handler.local_chain import local_summarizer_chain
from fastapi import HTTPException
from datetime import datetime
collection_name = "documents_01"
from Summary_Handler.local_translatorAgent import Local_TranslationAgent

@app.post("/api/createSummary")
def write_summary():
    try:
        start_time = datetime.now()
        print("API hívás megkezdődött:", start_time.strftime("%Y-%m-%d %H:%M:%S"))
        isStoreInLocal= input_data.get("stored_data", {}).get("isStoreInLocal", "default")

        if isStoreInLocal:
            output = local_summarizer_chain(input_data)
        else:
            output = global_summarizer_chain(input_data)
        
        final_summary = output.get("final_summary", "A végeredmény sikertelen.")
        print("API hívás véget ért.")

        #TIME
        end_time = datetime.now()
        elapsed_time = end_time - start_time
        elapsed_minutes = elapsed_time.total_seconds() // 60
        elapsed_seconds = elapsed_time.total_seconds() % 60
        print(f"Futási idő: {int(elapsed_minutes)} perc {int(elapsed_seconds)} másodperc.")

        return {"final_summary": final_summary}

    except HTTPException as e:
        print(f"HTTPException: {str(e)}")
        raise e
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    
##########################################################################
# Question and Answer
##########################################################################
from Models_Handler.global_model import GPT4
from Models_Handler.local_model import LLAMA
class QueryRequest(BaseModel):
    query: str

@app.post("/askmodel")
async def ask_model(request: QueryRequest):
    gpt_model = GPT4()
    llama_model = LLAMA()
    isStoreInLocal= input_data.get("stored_data", {}).get("isStoreInLocal", "default")

    if isStoreInLocal:
        answer = await llama_model.generate_response(request.query, collection_name)
    else:
        answer = gpt_model.generate_gpt4_response(request.query, collection_name)

    print(f"Kérdés: {request.query}")
    return {"response": answer}


