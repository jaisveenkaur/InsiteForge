# Research Console Webapp

This is a framework-free web UI for the FastAPI backend.

## Run locally

1. Start backend:
```bash
uvicorn api.main:app --reload
```

2. Serve frontend (any static server):
```bash
cd webapp
python3 -m http.server 5500
```

3. Open:
- http://127.0.0.1:5500

## Configuration

Edit `config.js`:
- `API_BASE_URL` (default: http://127.0.0.1:8000)
- default dataset filenames if no uploads are mapped

## Notes

- Uploads are parsed in-browser and sent inline to the API as JSON arrays.
- For large datasets, prefer server-side files and update `DEFAULT_SOURCES` instead.
- If API auth is enabled, provide the `x-api-key` value in the UI field.
