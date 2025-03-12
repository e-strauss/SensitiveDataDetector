# Sensitive Data Detector   

A PyQt6-based GUI tool for detecting and selecting sensitive information in text. The backend suggests candidates, and users can manually refine the selection.

## Features  
✅ **Automatic Detection** – Backend suggests sensitive words  
✅ **Manual Selection** – Right-click to select/unselect words  
✅ **Highlighting** – Detected words in red, user-selected in blue  
✅ **Anonymization** – Replaces sensitive words with placeholders  

## Installation  
1. Clone the repo:  
   ```sh
   git clone https://github.com/e-strauss/SensitiveDataDetector  
   cd SensitiveDataSelector

2. Create a virtual environment & install dependencies:
   ```sh
   python -m venv .venv  
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate  
   pip install -r requirements.txt  

3. Install GUI linux dependencies
   ```shell
   sudo apt update
   sudo apt install libxcb-cursor0 libxcb-xinerama0 libxcb-randr0 libxcb-shape0

4. Run the backend
   ```sh
   uvicorn main:app --reload

5. Run the GUI
   ```sh
   python gui.py