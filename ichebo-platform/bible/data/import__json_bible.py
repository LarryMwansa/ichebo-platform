import json
from sqlmodel import Session
from app.models import Verse
from app.database import engine
from app.book_meta import BOOKS  # ✅ using metadata

def load_bible_json(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def import_verses(data, version="WEB"):
    rows = data["resultset"]["row"]
    with Session(engine) as session:
        for row in rows:
            fields = row["field"]
            if len(fields) < 5:
                continue
            book_number = int(fields[1])
            meta = BOOKS.get(book_number, {"name": "Unknown", "testament": "Unknown"})

            verse = Verse(
                book=meta["name"],
                book_number=book_number,
                testament=meta["testament"],
                chapter=int(fields[2]),
                verse=int(fields[3]),
                text=fields[4].strip(),
                version=version
            )
            session.add(verse)
        session.commit()
    print(f"✅ Imported {len(rows)} verses.")

if __name__ == "__main__":
    data = load_bible_json("t_web.json")
    import_verses(data, version="WEB")
