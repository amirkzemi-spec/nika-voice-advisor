from db.models import init_db, SessionLocal, VisaProgram, Scholarship
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def seed():
    init_db()
    db = SessionLocal()

    # --- Visa programs ---
    db.add_all([
        VisaProgram(
            country="Netherlands",
            program="Startup Visa",
            validity="1 year (renewable)",
            requirements="Facilitator approval, innovative idea, registration with KvK, proof of funds.",
            fee="€350"
        ),
        VisaProgram(
            country="Germany",
            program="Student Visa",
            validity="Duration of study",
            requirements="University admission letter, blocked account (€11,208), health insurance.",
            fee="€75"
        )
    ])

    # --- Scholarships ---
    db.add_all([
        Scholarship(
            title="University of Twente Scholarship",
            country="Netherlands",
            degree_level="Master’s",
            funding_type="Partial",
            deadline="May 1, 2025",
            min_gpa=3.0,
            description="Covers tuition fees up to €12,000 for outstanding students."
        ),
        Scholarship(
            title="Swiss Excellence Fellowship",
            country="Switzerland",
            degree_level="PhD",
            funding_type="Full",
            deadline="Nov 30, 2025",
            min_gpa=3.2,
            description="Full financial support for international researchers."
        )
    ])

    db.commit()
    db.close()
    print("✅ Database seeded.")

if __name__ == "__main__":
    seed()
