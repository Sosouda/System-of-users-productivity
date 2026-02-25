import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from local_db.models import Base, TaskType

def create_template_db():
    db_path = os.path.join(os.path.dirname(__file__), "local_db", "SPS.db")

    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️  Старая БД удалена: {db_path}")

    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    print(f"✅ Структура БД создана: {db_path}")

    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        initial_types = [
            "Other", "Meeting", "Dust Cleaning", "Documentation",
            "Customer Support", "Code Bug Fix", "Research",
            "Optimization", "Deployment", "Project Management",
            "Feature Development"
        ]
        session.add_all([TaskType(name=t) for t in initial_types])
        session.commit()
        print("✅ Начальные данные добавлены")
    finally:
        session.close()

    print(f"\n📦 Шаблон БД готов для сборки!")
    print(f"   Размер: {os.path.getsize(db_path)} байт")

if __name__ == "__main__":
    create_template_db()
