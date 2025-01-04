import requests
from bs4 import BeautifulSoup
import re
import json
import logging
import urllib.parse
from pathlib import Path
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import threading
import curses

# Configure logging
logging.basicConfig(level=logging.DEBUG, filename='debug.log',
                    format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://pilvilinna.elisa.fi"
LOGIN_PAGE_URL = BASE_URL
PROTECTED_URL = BASE_URL

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Request-Reason": "Trying-to-get-my-data-out-from-the-cloud",
}

def extract_token(session):
    """Extract the login token from the login page."""
    response = session.get(LOGIN_PAGE_URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    token_input = soup.find('input', {'name': 'token'})
    if token_input:
        return token_input["value"]
    logging.debug("Token HTML: " + str(response.text))
    return None

def login(session, username, password):
    """Login to the website."""
    token = extract_token(session)
    if token is None:
        logging.error("Token extraction failed.")
        return False

    payload = {"us": username, "ps": password, "token": token}
    response = session.post(LOGIN_PAGE_URL, headers=HEADERS, data=payload)
    logging.info(f"Login Response: {response.status_code}")
    return response.ok

def fetch_js_content(session, script_path):
    """Fetch the JavaScript content to extract 'sf' and JSON data URL."""
    script_url = urllib.parse.urljoin(BASE_URL, script_path)
    response = session.get(script_url, headers=HEADERS)
    if response.status_code == 200:
        logging.info(f"Fetched JS from {script_url}")
        js_content = response.text

        # Extract 'sf' value
        match_sf = re.search(r"sf\s*:\s*'(\w+)'", js_content)
        sf_value = match_sf.group(1) if match_sf else None

        # Extract JSON data URL
        match_url = re.search(r"url:\s*'([^']+)'", js_content)
        json_data_url = match_url.group(1) if match_url else None

        return sf_value, json_data_url
    else:
        logging.error(f"Failed to fetch JS from {script_url}. Status: {response.status_code}")
    return None, None

def access_protected_page(session):
    """Access the protected page and extract the 'sf' value and JSON data URL."""
    response = session.get(PROTECTED_URL, headers=HEADERS)
    if response.status_code == 200:
        logging.info("Successfully accessed protected page.")
        soup = BeautifulSoup(response.content, "html.parser")
        scripts = soup.find_all('script', src=True)
        for script in scripts:
            js_src = script['src']
            if 'v=' in js_src:
                sf_value, json_data_url = fetch_js_content(session, js_src)
                if sf_value and json_data_url:
                    return sf_value, json_data_url
    else:
        logging.error(f"Failed to access page. Status code: {response.status_code}")
    return None, None

def get_media_data(session, email, json_data_url, media_type):
    """Fetch paginated JSON data containing media information."""
    
    cumulative_results = {
        "order": [],
        "files": {},
        "total": 0,
        "description": "",
        "code": 0
    }

    # URL encode the user
    user = urllib.parse.quote(email)

    def fetch_page_data(page):
        payload_post = {
            "type": media_type,
            "p": str(page),
            "d": user,
            "options[filter_sortby]": "",
            "options[filter_date_type]": "date_created",
            "options[filter_filename]": "",
            "options[start_date]": "",
            "options[end_date]": "",
            "options[device]": "",
        }
        full_url = urllib.parse.urljoin(BASE_URL, json_data_url)
        response = session.post(full_url, headers=HEADERS, data=payload_post)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Failed to fetch JSON data for {media_type}. Status code: {response.status_code}")
            return None

    page = 1  # Start with the first page
    total_fetched = 0
    total_files = None

    while True:
        data = fetch_page_data(page)
        
        if data and "files" in data and "order" in data:
            if total_files is None:
                total_files = int(data.get("total", 0))
                cumulative_results["total"] = total_files
                cumulative_results["description"] = data.get("description", "")
                cumulative_results["code"] = data.get("code", 0)

            files_data = data["files"]
            order_list = data["order"]

            # Append new data to cumulative results
            cumulative_results["order"].extend(order_list)
            cumulative_results["files"].update(files_data)

            # Update the total number of files fetched
            num_files_in_page = len(order_list)
            total_fetched += num_files_in_page

            # If we have fetched all files, break the loop
            if total_fetched >= total_files:
                break
            
            page += 1  # Move to the next page
            sleep(1) # Rate Limit, lets give the API a break
        else:
            break  # Exit if there's an error or data is unexpectedly structured

    return cumulative_results

def prepare_download_directories(json_data, base_download_path):
    """Prepare directories based on `date_uploaded` in `json_data`."""
    if 'files' in json_data:
        for file_info in json_data['files'].values():
            if 'date_uploaded' in file_info:
                date_uploaded = datetime.fromtimestamp(file_info['date_uploaded'], tz=timezone.utc).strftime('%Y-%m')
                download_path = Path(base_download_path) / date_uploaded
                download_path.mkdir(parents=True, exist_ok=True)
                file_info['download_path'] = str(download_path)

def download_file(stdscr, session, sf_value, file_info, lock, progress, worker_id):
    """Download a single file using provided data."""
    file_url = f"{BASE_URL}/cloudia_api/core/get_file?&flags=1&sfile={sf_value}&file={file_info['file']}"
    response = session.get(file_url, headers=HEADERS, stream=True)
    
    if response.status_code == 200:
        file_path = Path(file_info['download_path']) / file_info['filename']
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        with lock:
            progress['workers'][worker_id] = file_info['filename']
            progress['count'] += 1
            print_progress(stdscr, progress)
        logging.info(f"Downloaded {file_info['filename']} to {file_info['download_path']}")
    else:
        logging.error(f"Failed to download {file_info['filename']}. Status code: {response.status_code}")

def print_progress(stdscr, progress):
    """Print the progress in a fixed layout using curses."""
    stdscr.clear()
    lines = [f"Worker {i+1}: {filename}" for i, filename in enumerate(progress['workers'])]
    summary = f"Media type: processing {progress['count']}/{progress['total']}"
    for index, line in enumerate(lines):
        stdscr.addstr(index, 0, line)
    stdscr.addstr(len(lines), 0, "-"*30)
    stdscr.addstr(len(lines) + 1, 0, summary)
    stdscr.refresh()

def main_curses(stdscr):
    import secs  # Ensure this module provides 'username' and 'password'
    username = secs.username
    password = secs.password

    media_types = {
        "photos": "./downloads/kuvat/",
        "videos": "./downloads/videot/",
        "audio": "./downloads/audio/",
        "other": "./downloads/other/"
    }

    # Ensure all base directories exist
    for download_path in media_types.values():
        Path(download_path).mkdir(parents=True, exist_ok=True)

    for media_type, download_path in media_types.items():
        with requests.Session() as session:
            if login(session, username, password):
                sf_value, json_data_url = access_protected_page(session)
                if sf_value and json_data_url:
                    json_data = get_media_data(session, username, json_data_url, media_type)
                    json_file_path = f"{media_type}.json"

                    # Save fetched JSON data
                    with open(json_file_path, "w") as f:
                        f.write(json.dumps(json_data, indent=4))

                    # Prepare directories and update file information
                    prepare_download_directories(json_data, download_path)

                    # Download each file concurrently
                    if json_data and 'files' in json_data:
                        file_infos = list(json_data['files'].values())
                        progress = {'count': 0, 'total': len(file_infos), 'workers': [''] * 20}
                        lock = threading.Lock()
                        with ThreadPoolExecutor(max_workers=20) as executor:
                            for i, file_info in enumerate(file_infos):
                                executor.submit(download_file, stdscr, session, sf_value, file_info, lock, progress, i % 20)
                else:
                    logging.error("Failed to extract required values.")
            else:
                logging.error("Login failed.")

if __name__ == "__main__":
    curses.wrapper(main_curses)
