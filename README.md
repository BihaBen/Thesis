Rendszer indítása:

Várakozni szükséges még az NLTK csomagokat frissíti: C:\Users\Username\Appdata\Roaming\
- corpora
- taggers
- tokenizers

#FastAPI#
cd L:\Thesis\Backend
venv\Scripts\activate
uvicorn main:app --reload

Betöltés után a "http://localhost:5173/"-on szükséges nyomni egy refresh-t.
#Sveltekit#
cd L:\Thesis\Frontend\Sveltekit
npm run dev

#Qdrant Docker#
docker run -p 6333:6333 qdrant/qdrant