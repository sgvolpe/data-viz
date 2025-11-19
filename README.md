# Data Viz


# Useful Commands

Activate virtual environment
```
.\.venv\Scripts\activate
```
 
Install pipenv
 ```
pip install pipenv
 ```


Create New venv
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version

```

# Deploy

⭐ How to Use
Patch version (default):

1.2.3 → 1.2.4
```
powershell -File deploy.ps1 -patch "Fix: dashboard alignment issue"
```
Minor version:

1.2.3 → 1.3.0
```
powershell -File deploy.ps1 -minor "Feat: added charts section"
```
Major version:

1.2.3 → 2.0.0
```
powershell -File deploy.ps1 -major "BREAKING: reworked API"
```

⚡ Requirements

pytest installed (pipenv install pytest)

flake8 installed (pipenv install flake8)

black installed (pipenv install black)

mypy installed (pipenv install mypy)