from db.models import Base, engine

print("🚀 Creating database schema...")
Base.metadata.create_all(bind=engine)
print("✅ Database setup complete!")
