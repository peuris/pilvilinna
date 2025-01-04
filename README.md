
# Elisa Pilvilinna Cloud Backup Downloader

## Overview
This Python project facilitates downloading large amounts of media files (photos, videos, audio, and other files) from a cloud backup service (e.g., Elisa Pilvilinna), leveraging concurrent downloads, directory organization by upload date, and a user-friendly progress display using curses.

## Features
- **Automated Login**: Logs into the cloud service programmatically using provided credentials.
- **Dynamic Data Fetching**: Extracts necessary sf tokens and JSON data URLs for fetching media.
- **Concurrent Downloads**: Downloads multiple files concurrently using ThreadPoolExecutor.
- **Organized Directories**: Classifies files into directories based on their upload dates for better organization.
- **Progress Display**: Real-time terminal-based progress feedback using curses.
- **Error Logging**: Logs errors and debug information for better troubleshooting.

## Requirements
Ensure you have Python 3.7+ installed and the necessary dependencies.

## Dependencies
You can install the dependencies using pip (WSL2/Linux):
```bash
pip install -r requirements.txt
```
or
```bash
pip install requests==2.32.3 beautifulsoup4==4.12.3
```

If you're on *Windows* and need functionality similar to curses, you might need a package like windows-curses to provide compatibility:
```bash
pip install windows-curses
```

## Getting Started
1. **Clone the Repository**
```bash
git clone https://github.com/your-username/cloud-backup-downloader.git
cd cloud-backup-downloader
```
2. **Set Up Credentials**
This script assumes you have a separate Python file named `secs.py` to securely store your login credentials.
```python
username = "your-email@example.com"
password = "your-password"
```
3. **Run the Script**
To start downloading media files:
```bash
python pilvilinna.py
```
The files will be downloaded into the following default directory structure (depending on the media type):
```
downloads/
├── kuvat/  [Photos]
├── videot/ [Videos]
├── audio/  [Audio Files]
└── other/  [Other Files]
```
The script organizes files into subdirectories based on their upload month (e.g., "2023-10").

## How to Use
- **Login Process**: Provide your email and password in the `secs.py` file. The script will handle login and session management automatically.
- **Fetching Media Metadata**: The script dynamically fetches file metadata (e.g., filenames, upload dates) from the cloud service.
- **Download Files**: Downloads all files concurrently for each media type while showing the progress in the terminal.

## Configuration
### Download Paths
Default download paths for file types can be edited in the `main_curses()` function:
```python
media_types = {
    "photos": "./downloads/kuvat/",
    "videos": "./downloads/videot/",
    "audio": "./downloads/audio/",
    "other": "./downloads/other/"
}
```
### Rate Limiting
You can adjust the sleep duration between API requests (specified in seconds) for rate-limiting compliance:
```python
sleep(1)  # Adjust the delay as needed (default: 1 second)
```

## File Structure
Filename | Description
--- | ---
`pilvilinna.py` | Main script for logging in, data fetching, and downloading files.
`secs.py` | Credential storage. Ensure to keep this file secure.
`requirements.txt` | List of dependencies for pip installation.
`debug.log` (generated) | Log file for debugging during execution.

## Logging
All debug information, errors, and significant events are logged to the `debug.log` file. You can review this file to troubleshoot unexpected behavior.

## Known Limitations
- **Account-Specific**: The script assumes the cloud service UI and API have not changed. Adjustments might be needed if the structure or endpoints of the website change.
- **Rate Limits**: The cloud service may enforce rate limits on API calls. You may need to increase sleep duration for smoother operation.
- **Concurrency Limits**: Default to 20 concurrent downloads; you can adjust this value for better system performance.

## Future Enhancements
- Add support for retry logic in case of failed downloads.
- Implement resume functionality to continue from interrupted sessions.
- Provide a GUI version for users unfamiliar with the terminal environment.
- Add an option for filtering media by date ranges or types before downloading.

## Contributing
Contributions are welcome! Feel free to submit an issue or a pull request.
- **Fork the repository**.
- **Create your feature branch**.
```bash
git checkout -b feature/your-feature-name
```
- **Commit your changes**.
```bash
git commit -am "Add your message here"
```
- **Push to the branch**.
```bash
git push origin feature/your-feature-name
```
- **Open a Pull Request**.

## Security Advisory
- Store your credentials (`secs.py`) securely and ensure it is never shared or pushed to public repositories.
- Avoid hardcoding sensitive information directly in the script.

## License
This project is licensed under the MIT License.

## Disclaimer
This script is intended for personal use only. Ensure you comply with the terms of service of the cloud provider before using this tool. The author assumes no liability for unintended consequences resulting from your usage of this script.
