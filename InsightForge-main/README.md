# InsightForge

InsightForge is an e-commerce intelligence research agent designed to help teams synthesize fragmented data across catalogs, reviews, pricing, and competitor listings into strategic business decisions.

By analyzing raw data inputs, InsightForge generates comprehensive, evidence-based reports. The system offers a "Quick" mode for rapid insights and a "Deep" mode for comprehensive strategic analysis, eliminating the need to manually interpret basic metrics.

## Key Features

- Quick mode for rapid insights and Deep mode for comprehensive strategy analysis.
- Actionable business recommendations based on evidence-backed data synthesis.
- Automated data completeness checks and noise detection.
- Persistent memory to adapt to user preferences over time.
- Fully functional API built with FastAPI.
- Interactive web dashboard for streamlined use.

## Project Structure

- `src/research_agent.py`: The core research engine
- `api/`: FastAPI backend with rate limiting, logging, and validation
- `webapp/`: The frontend UI dashboard
- `data/domain_memory.json`: Where the agent's memory is stored
- `datasets/`: Processed datasets for sample runs

### 1. API Backend Setup

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Then start the FastAPI server:

```bash
uvicorn api.main:app --reload
```

You can check out the API docs at `http://127.0.0.1:8000/docs`.

### 2. Run the Web Dashboard

Open a new terminal window, navigate to the webapp folder, and start a local server:

```bash
cd webapp
python3 -m http.server 5500
```

Open your browser to `http://127.0.0.1:5500` to use the interface.

### Running via CLI

If you prefer the command line, you can run the agent directly:

Quick report:

```bash
python3 src/research_agent.py --brief examples/brief_quick_underperforming.json --output out/quick_report.md --update-memory
```

Deep report:

```bash
python3 src/research_agent.py --brief examples/brief_deep_gap_analysis.json --output out/deep_report.md --update-memory
```

## Datasets

I've included processed JSON datasets in `datasets/processed/` that work out of the box. If you want to use the raw CSV files, you'll need Git LFS:

```bash
git lfs install
git lfs pull
```

## Production Configuration

The API includes a built-in rate limiter (30 requests per minute) and structured logging. API key authentication can be enabled by setting the `ECOM_AGENT_API_KEY` environment variable.

## License

MIT
