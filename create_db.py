from app import create_app, db

app = create_app()

# Create the database and tables
with app.app_context():
    db.create_all()
