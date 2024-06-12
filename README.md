# 🚀 GitHub Commits Fetcher

GitHub Commits Fetcher is a Python application that allows users to fetch commit details from a GitHub repository, display commits in a user-friendly manner, save commit data to a CSV file, and download files associated with commits.

## Features

- Fetch branches of a GitHub repository.
- Fetch commits within a specified date range for a selected branch.
- Display fetched commits with detailed information such as author, date, message, filename, status, additions, deletions, and raw URL.
- Save commit data to a CSV file for further analysis.
- Download files associated with commits directly from the application.

## Prerequisites

Before running the application, ensure you have the following:

- Python 3.x installed on your machine. 🐍
- Required Python packages installed (`requests`, `dotenv`, `tkinter`, `tkcalendar`, `pytz`). 📦

## Installation and Usage

1. Clone the repository to your local machine:
   ```bash
   git clone https://github.com/YatharthBhatia/Commit-Tracker.git

2. Install the required Python packages using pip:
   ```bash
   pip install -r requirements.txt

3. Set up your GitHub token:
- Create a `.env` file in the project root directory.
- Add your GitHub token in the `.env` file:
  ```
  GITHUB_TOKEN=your_github_token_here
  ```

4. Run the application:
   ```bash
   python main.py

5. Enter the GitHub repository URL, select a branch, choose date range, and click "Fetch Commits" to get started. 🚀

## Screenshots

![image](https://github.com/YatharthBhatia/Commit-Tracker/assets/124282341/5b20db90-a181-475f-9f11-3c6ec15b0bf1)
![image](https://github.com/YatharthBhatia/Commit-Tracker/assets/124282341/79f6ab71-a6cc-4ae0-acbb-57af84c481ed)

