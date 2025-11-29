"""Download spaCy models."""

import subprocess
import sys


def download_model(model_name: str):
    """Download a spaCy model."""
    print(f"Downloading {model_name}...")
    try:
        subprocess.run([sys.executable, "-m", "spacy", "download", model_name], check=True)
        print(f"✓ {model_name} downloaded successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to download {model_name}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("Downloading spaCy models...")
    download_model("tr_core_news_lg")
    download_model("en_core_web_lg")
    print("All models downloaded successfully!")

