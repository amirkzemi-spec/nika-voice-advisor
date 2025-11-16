from pathlib import Path

def extract_metadata(file_path: Path):
    name = file_path.stem.lower()

    # detect country
    country = name.split("_")[0]

    # detect visa type
    visa_type = "unknown"
    if "study" in name: visa_type = "study"
    if "startup" in name: visa_type = "startup"
    if "work" in name: visa_type = "work"
    if "residence" in name: visa_type = "residence"
    if "family" in name: visa_type = "family"

    return {
        "country": country,
        "visa_type": visa_type,
        "source": file_path.name
    }
