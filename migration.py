from app import db, create_app
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as connection:
        connection.execute(text("ALTER TABLE summary ADD COLUMN summary_type VARCHAR(255)"))
    db.create_all()
    print("Database migrated successfully!")
