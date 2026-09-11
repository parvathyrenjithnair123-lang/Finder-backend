from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer, util
from sqlalchemy.orm import Session
from database import SessionLocal, init_db, TitleModel
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = SentenceTransformer('all-MiniLM-L6-v2')

corpus_items = []
corpus_embeddings = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def safe_list(val) -> List[str]:
    """Ensures input is always a list of strings, avoiding join crashes."""
    if isinstance(val, list):
        return [str(i) for i in val]
    return []

def refresh_embeddings(db: Session):
    global corpus_items, corpus_embeddings
    
    titles = db.query(TitleModel).all()

    corpus_items = [
        {
            "id": str(t.id),
            "title": t.title or "",
            "type": t.type or "MANHWA",
            "coverUrl": t.coverUrl or "",
            "description": t.description or "",
            "country": t.country or "South Korea",
            "year": t.year or 2024,
            "genres": safe_list(t.genres),
            "tags": safe_list(t.tags),
            "rating": float(t.rating) if t.rating else 0.0,
            "whereToWatch": safe_list(t.whereToWatch),
        }
        for t in titles
    ]

    corpus_texts = [
        f"{item['title']}. {item['description']} Genres: {', '.join(item['genres'])}. Tropes: {', '.join(item['tags'])}"
        for item in corpus_items
    ]
    
    if corpus_texts:
        corpus_embeddings = model.encode(corpus_texts, convert_to_tensor=True)

@app.on_event("startup")
def startup_event():
    init_db()
    db = SessionLocal()
    refresh_embeddings(db)
    db.close()

# --- MISSING GET ROUTE ADDED HERE ---
@app.get("/titles")
def get_all_titles(db: Session = Depends(get_db)):
    return corpus_items

@app.get("/search")
def search_titles(q: str = ""):
    query = q.strip()
    if not query or corpus_embeddings is None or len(corpus_items) == 0:
        return corpus_items

    query_embedding = model.encode(query, convert_to_tensor=True)
    cosine_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]

    ranked_results = []
    for idx, score in enumerate(cosine_scores):
        item = corpus_items[idx].copy()
        item["score"] = float(score)
        ranked_results.append(item)

    ranked_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return ranked_results

class TitleCreate(BaseModel):
    id: str
    title: str
    type: Optional[str] = "MANHWA"
    coverUrl: Optional[str] = ""
    description: Optional[str] = ""
    country: Optional[str] = "South Korea"
    year: Optional[int] = 2024
    genres: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    rating: Optional[float] = 0.0
    whereToWatch: Optional[List[str]] = []

@app.post("/titles")
def create_title(title: TitleCreate, db: Session = Depends(get_db)):
    db_title = TitleModel(**title.model_dump())
    db.add(db_title)
    db.commit()
    refresh_embeddings(db)
    return {"status": "success", "message": f"Added {title.title}"}