import xml.etree.ElementTree as ET
from sqlmodel import Session
from app.models import Verse
from app.database import engine
from app.book_meta import BOOKS  # ✅ ← this line connects it

def import_xml_bible(filepath: str, version="NKJV"):
    tree = ET.parse(filepath)
    root = tree.getroot()

    with Session(engine) as session:
        for biblebook in root.findall("BIBLEBOOK"):
            bnumber = int(biblebook.get("bnumber"))
            meta = BOOKS.get(bnumber, {"name": "Unknown", "testament": "Unknown"})
            for chapter in biblebook.findall("CHAPTER"):
                chapter_num = int(chapter.get("cnumber"))
                for verse in chapter.findall("VERS"):
                    verse_num = int(verse.get("vnumber"))
                    text = verse.text.strip() if verse.text else ""
                    verse_obj = Verse(
                        book=meta["name"],
                        book_number=bnumber,
                        testament=meta["testament"],
                        chapter=chapter_num,
                        verse=verse_num,
                        text=text,
                        version=version
                    )
                    session.add(verse_obj)
        session.commit()
    print("✅ XML Bible import complete.")
