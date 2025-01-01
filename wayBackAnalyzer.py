import requests
from bs4 import BeautifulSoup
import argparse
from urllib.parse import urljoin, urlparse
from waybackpy import WaybackMachineCDXServerAPI
import os

def get_wayback_snapshots(url, max_snapshots=10):
    """
    Retrieve Wayback Machine snapshots for the given URL.
    """
    print(f"Fetching Wayback Machine snapshots for: {url}")
    cdx = WaybackMachineCDXServerAPI(url)
    snapshots = []
    try:
        for archive in cdx.snapshots():
            snapshots.append(archive.archive_url)
            if len(snapshots) >= max_snapshots:
                break
    except Exception as e:
        print(f"Error fetching snapshots: {e}")
    return snapshots

def is_valid_http_url(url):
    """
    Check if a URL is valid for HTTP/HTTPS requests.
    """
    parsed_url = urlparse(url)
    return parsed_url.scheme in ["http", "https"]

def extract_links(base_url, html_content):
    """
    Extract all valid HTTP/HTTPS links from HTML content.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    links = set()
    for tag in soup.find_all("a", href=True):
        link = urljoin(base_url, tag["href"])
        if is_valid_http_url(link):
            links.add(link)
    return links

def extract_files(base_url, html_content):
    """
    Extract potential files (like PDFs, images, etc.) from HTML content.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    files = set()
    for tag in soup.find_all(["a", "img", "script", "link"], {"href": True, "src": True}):
        attr = tag.get("href") or tag.get("src")
        if attr:
            file_url = urljoin(base_url, attr)
            parsed_url = urlparse(file_url)
            if is_valid_http_url(file_url) and any(
                parsed_url.path.endswith(ext)
                for ext in [".pdf", ".doc", ".zip", ".jpg", ".png", ".js", ".css", ".php", "="]
            ):
                files.add(file_url)
    return files

def crawl_website(base_url, max_depth=2):
    """
    Crawl the website recursively to extract links and files.
    """
    visited = set()
    to_visit = {base_url}
    all_links = set()
    all_files = set()

    for depth in range(max_depth):
        next_to_visit = set()
        print(f"Crawling depth {depth + 1}...")
        for url in to_visit:
            if url in visited:
                continue
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    visited.add(url)
                    links = extract_links(url, response.text)
                    files = extract_files(url, response.text)
                    all_links.update(links)
                    all_files.update(files)
                    next_to_visit.update(links - visited)
            except requests.RequestException as e:
                print(f"Error fetching {url}: {e}")
        to_visit = next_to_visit

    return all_links, all_files

def save_to_file(filename, data, filter_in=None, filter_out=None):
    """
    Save extracted data to a file and apply optional filtering.
    - filter_in: Include only lines containing these substrings (list of strings).
    - filter_out: Exclude lines containing these substrings (list of strings).
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    filtered_data = data

    # Apply filter_in
    if filter_in:
        filtered_data = [line for line in filtered_data if any(keyword in line for keyword in filter_in)]

    # Apply filter_out
    if filter_out:
        filtered_data = [line for line in filtered_data if not any(keyword in line for keyword in filter_out)]

    # Save filtered data
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(filtered_data))
    print(f"Saved to {filename}")

def get_domain_name(url):
    """
    Extract the domain name from a URL.
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    # Remove 'www.' if present
    if domain.startswith("www."):
        domain = domain[4:]
    return domain

def main():
    parser = argparse.ArgumentParser(description="Deep analyze a website for files, folders, and historical data.")
    parser.add_argument("url", help="Target website URL")
    parser.add_argument("--max-depth", type=int, default=2, help="Max crawl depth (default: 2)")
    parser.add_argument("--max-snapshots", type=int, default=10, help="Max Wayback Machine snapshots to retrieve")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    domain_name = get_domain_name(base_url)
    output_dir = domain_name  # Use the domain name as the output folder

    # Fetch Wayback Machine snapshots
    snapshots = get_wayback_snapshots(base_url, args.max_snapshots)
    save_to_file(os.path.join(output_dir, "wayback_snapshots.txt"), snapshots)

    # Crawl the website
    all_links, all_files = crawl_website(base_url, args.max_depth)

    # Define filters for links.txt
    filter_in_keywords = [".com", ".org"]  # Include links with these substrings
    filter_out_keywords = ["facebook", "twitter"]  # Exclude links with these substrings

    # Save filtered links
    save_to_file(os.path.join(output_dir, "links.txt"), all_links, filter_in=filter_in_keywords, filter_out=filter_out_keywords)

    # Save files without filters
    save_to_file(os.path.join(output_dir, "files.txt"), all_files)

    print("Analysis complete!")
    print(f"Output saved in folder: {output_dir}")
    print(f"Wayback snapshots: {len(snapshots)} saved.")
    print(f"Links: {len(all_links)} found and saved.")
    print(f"Files: {len(all_files)} found and saved.")

if __name__ == "__main__":
    main()
