# Pedomerger (Streamlit + Python)

A Python-only Streamlit app for PDF and image utilities.

## Features
- Merge multiple PDFs with ordering controls
- Split a PDF by page range
- Rotate all PDF pages or a selected range
- Convert PDF pages to JPG (single JPG or ZIP of multiple pages)
- Convert multiple JPG/JPEG/PNG images into a PDF with ordering controls
- Crop images by specifying pixel coordinates
- Custom output filenames and previews
- Light and dark appearance modes

## Run locally

Recommended: Python 3.11 or 3.12.

```bash
python -m venv .venv
```

Activate the environment:

**macOS/Linux**
```bash
source .venv/bin/activate
```

**Windows**
```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies and start:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

The app will show a local URL, normally http://localhost:8501.

## Deploy to Streamlit Community Cloud
1. Create a GitHub repository and upload `app.py`, `requirements.txt`, and `README.md`.
2. Go to https://share.streamlit.io/ and sign in with GitHub.
3. Select the repository and branch, then set the main file path to `app.py`.
4. Deploy.

## Notes
- Files are processed by the Python process hosting the app. For public hosting, do not upload sensitive documents unless you trust the deployment host.
- Large PDFs can require significant RAM. PDF-to-JPG resolution increases memory use.
- The crop tool uses pixel coordinates, not drag-to-crop. A drag cropper can be added later using a Streamlit-compatible crop component.
- Streamlit is a web app framework; it does not compile a native Android APK by itself. It works in Android and iPhone browsers.
