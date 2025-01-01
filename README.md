# Website wayBackAnalyzer

This script analyzes a given website to extract:
- Historical snapshots from the Wayback Machine.
- Valid HTTP/HTTPS links.
- Files like PDFs, images, and scripts.

## Features
- Fetches Wayback Machine snapshots for a URL.
- Crawls a website recursively to extract links and files.
- Saves extracted data to organized folders.

## Requirements
- Python 3.8+
- `beautifulsoup4`
- `requests`
- `waybackpy`

## Installation
1. Clone this repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt

## Usage
   `python wayBackAnalyzer.py <URL> --max-depth 3 --max-snapshots 15`
