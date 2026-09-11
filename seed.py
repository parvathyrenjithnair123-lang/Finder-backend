import json
from database import SessionLocal, TitleModel, init_db
from main import refresh_embeddings

def seed_from_json():
    init_db()
    db = SessionLocal()
    
    with open("data.json", "r", encoding="utf-8") as f:
        titles = json.load(f)
        
    for item_data in titles:
        existing = db.query(TitleModel).filter(TitleModel.id == item_data["id"]).first()
        if not existing:
            db_title = TitleModel(**item_data)
            db.add(db_title)
            print(f"  ✅ Added: {item_data['title']}")
        else:
            print(f"  ⚠️ Skipped (already exists): {item_data['title']}")
            
    db.commit()
    print("\nRefreshing AI vector embeddings...")
    refresh_embeddings(db)
    db.close()
    print("Done!")

if __name__ == "__main__":
    seed_from_json()