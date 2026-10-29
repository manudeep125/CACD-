# PhishGuard AI
AI-powered phishing email and URL detection. Stack: Python, Flask, Scikit-learn, SQLite, Bootstrap, Chart.js.

## Windows + VS Code setup
1. Install Python 3.10+ (tick "Add Python to PATH"). Unzip the project and open the folder in VS Code (File > Open Folder).
2. Open the terminal (Ctrl+`) and run:
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python generate_dataset.py
python train_model.py
python app.py
```
If PowerShell blocks activation: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
3. Open http://127.0.0.1:5000
4. Run tests: `python -m unittest tests.test_app -v`

## Using a real dataset
Replace data/emails.csv (columns: text,label) and data/urls.csv (columns: url,label; 1 = phishing, 0 = safe), then run `python train_model.py`.
