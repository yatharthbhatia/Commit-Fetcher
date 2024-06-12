import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
import webbrowser
import csv
import pytz
from datetime import datetime
import os
from tkinter import Scrollbar

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

def fetch_branches(repo_url):
    parts = repo_url.rstrip('/').split('/')
    owner = parts[-2]
    repo = parts[-1]
    
    api_url = f'https://api.github.com/repos/{owner}/{repo}/branches'
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}'
    }

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        return [branch['name'] for branch in response.json()]
    else:
        messagebox.showerror("Error", f"Failed to fetch branches: {response.status_code}")
        return None

def fetch_commits(repo_url, branch, since, until):
    parts = repo_url.rstrip('/').split('/')
    owner = parts[-2]
    repo = parts[-1]

    api_url = f'https://api.github.com/repos/{owner}/{repo}/commits'
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}'
    }

    params = {
        'sha': branch,
        'since': since,
        'until': until
    }

    response = requests.get(api_url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        messagebox.showerror("Error", f"Failed to fetch commits: {response.status_code}")
        return None

def download_file(file_url):
    response = requests.get(file_url, headers={'Authorization': f'token {GITHUB_TOKEN}'})
    if response.status_code == 200:
        filename = file_url.split('/')[-1]
        with open(filename, 'wb') as file:
            file.write(response.content)
        messagebox.showinfo("Success", f"File downloaded to {filename}")
    else:
        messagebox.showerror("Error", f"Failed to download file: {response.status_code}")

def download_callback(url):
    download_file(url)

def save_commit_text_and_exit(commit_text):
    with open("previous_session.txt", "w") as file:
        text_content = commit_text.get("1.0", tk.END)
        file.write(text_content)
    root.destroy()

def save_to_csv():
    global commits
    if not commits:
        messagebox.showerror("Error", "No commits fetched. Please fetch commits first.")
        return

    with filedialog.asksaveasfile(mode='w', defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]) as csvfile:
        if csvfile is not None:
            fieldnames = ['Author', 'Date', 'Message', 'Filename', 'Status', 'Additions', 'Deletions', 'Raw URL']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for commit in commits:
                commit_message = commit['commit']['message']
                author_name = commit['commit']['author']['name']
                commit_date = commit['commit']['author']['date']

                commit_details = fetch_commit_details(commit['url'])
                if commit_details and 'files' in commit_details:
                    for file in commit_details['files']:
                        filename = file['filename']
                        additions = file['additions']
                        deletions = file['deletions']
                        status = file['status']
                        raw_url = file['raw_url']

                        # Check if any field is empty before writing the row
                        if author_name and commit_date and commit_message and filename and status and additions is not None and deletions is not None and raw_url:
                            writer.writerow({'Author': author_name, 'Date': commit_date, 'Message': commit_message,
                                             'Filename': filename, 'Status': status, 'Additions': additions,
                                             'Deletions': deletions, 'Raw URL': raw_url})
            messagebox.showinfo("Success", f"Data saved to {csvfile.name}")
        else:
            messagebox.showerror("Error", "File save operation canceled.")


def display_commits():
    repo_url = repo_url_entry.get()
    branch = branch_combobox.get()
    since = since_date_entry.get_date().isoformat()
    until = until_date_entry.get_date().isoformat()
    
    try:
        datetime.strptime(since, '%Y-%m-%d')
        datetime.strptime(until, '%Y-%m-%d')
    except ValueError:
        messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD.")
        return
    
    global commits
    commits = fetch_commits(repo_url, branch, since, until)
    
    if commits:
        commit_frame = tk.Frame(mainframe)
        commit_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))

        commit_text = tk.Text(commit_frame, wrap="none", width=180, height=40)
        commit_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        scroll_x = Scrollbar(commit_frame, orient=tk.HORIZONTAL, command=commit_text.xview)
        commit_text.configure(xscrollcommand=scroll_x.set)
        scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))

        commit_text.config(state=tk.NORMAL)
        commit_text.delete("1.0", tk.END)


        header = "Author".ljust(20) + "Date".ljust(30) + "Message".ljust(60) + "Filename".ljust(40) + \
                 "Status".ljust(15) + "Additions".ljust(10) + "Deletions".ljust(10) + "\n"
        commit_text.insert(tk.END, header)
        commit_text.insert(tk.END, "-" * 190 + "\n")

        for commit in commits:
            commit_message = commit['commit']['message']
            author_name = commit['commit']['author']['name']
            commit_date_utc = commit['commit']['author']['date']
            commit_date_utc = datetime.strptime(commit_date_utc, '%Y-%m-%dT%H:%M:%SZ')
            ist = pytz.timezone('Asia/Kolkata')
            commit_date_ist = commit_date_utc.astimezone(ist)
            commit_date_ist_str = commit_date_ist.strftime('%Y-%m-%d %H:%M:%S IST')

            commit_details = fetch_commit_details(commit['url'])
            if commit_details and 'files' in commit_details:
                for file in commit_details['files']:
                    filename = file['filename']
                    additions = file['additions']
                    deletions = file['deletions']
                    status = file['status']
                    raw_url = file['raw_url']

                    row = f"{author_name.ljust(20)}{commit_date_ist_str.ljust(25)}{commit_message.ljust(60)}" \
                          f"{filename.ljust(38)}{status.ljust(15)}{str(additions).ljust(15)}{str(deletions).ljust(15)}"

                    commit_text.insert(tk.END, row + '\n')

                    
                    commit_text.insert(tk.END, ' ' * 100)
                    download_button = tk.Button(commit_text, text=f'Download {filename}', fg='blue', cursor='hand2',
                                                command=lambda url=raw_url: download_callback(url))
                    commit_text.window_create(tk.END, window=download_button)
                    commit_text.insert(tk.END, '\n')

        save_csv_button = ttk.Button(mainframe, text="Save to CSV", command=save_to_csv)
        save_csv_button.grid(row=7, column=2, sticky=tk.W)       
        
        commit_text.config(state=tk.DISABLED)
        
        root.protocol("WM_DELETE_WINDOW", lambda: save_commit_text_and_exit(commit_text))


    else:
        messagebox.showerror("Error", "No commits fetched.")

def update_branches():
    repo_url = repo_url_entry.get()
    branches = fetch_branches(repo_url)
    if branches:
        branch_combobox['values'] = branches
        branch_combobox.set(branches[0])

def fetch_commit_details(commit_url):
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}'
    }
    
    response = requests.get(commit_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None
    

root = tk.Tk()
root.title("GitHub Commits Fetcher")

mainframe = ttk.Frame(root, padding="10")
mainframe.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

repo_url_label = ttk.Label(mainframe, text="GitHub Repository URL:")
repo_url_label.grid(row=1, column=1, sticky=tk.W)
repo_url_entry = ttk.Entry(mainframe, width=50)
repo_url_entry.grid(row=1, column=2, sticky=(tk.W, tk.E))

fetch_branches_button = ttk.Button(mainframe, text="Fetch Branches", command=update_branches)
fetch_branches_button.grid(row=1, column=3, sticky=tk.W)

branch_label = ttk.Label(mainframe, text="Branch:")
branch_label.grid(row=2, column=1, sticky=tk.W)
branch_combobox = ttk.Combobox(mainframe, state="readonly")
branch_combobox.grid(row=2, column=2, sticky=(tk.W, tk.E))

since_date_label = ttk.Label(mainframe, text="Start Date:")
since_date_label.grid(row=3, column=1, sticky=tk.W)
since_date_entry = DateEntry(mainframe, width=12, background='darkblue',
                             foreground='white', borderwidth=2, year=2024, date_pattern="dd-mm-yyyy")
since_date_entry.grid(row=3, column=2, sticky=(tk.W, tk.E))

until_date_label = ttk.Label(mainframe, text="End Date:")
until_date_label.grid(row=4, column=1, sticky=tk.W)
until_date_entry = DateEntry(mainframe, width=12, background='darkblue',
                             foreground='white', borderwidth=2, year=2024, date_pattern="dd-mm-yyyy")
until_date_entry.grid(row=4, column=2, sticky=(tk.W, tk.E))

fetch_button = ttk.Button(mainframe, text="Fetch Commits", command=display_commits)
fetch_button.grid(row=5, column=2, sticky=tk.W)

# commit_text = tk.Text(mainframe, wrap="word", width=180, height=40)
# commit_text.grid(row=6, column=1, columnspan=2, sticky=(tk.W, tk.E))

commit_frame = tk.Frame(mainframe)
commit_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))

commit_text = tk.Text(commit_frame, wrap="none", width=180, height=40)
commit_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

scroll_x = Scrollbar(commit_frame, orient=tk.HORIZONTAL, command=commit_text.xview)
commit_text.configure(xscrollcommand=scroll_x.set)
scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))

commit_text.config(state=tk.NORMAL)
commit_text.delete("1.0", tk.END)

commit_scroll = ttk.Scrollbar(mainframe, orient=tk.VERTICAL, command=commit_text.yview)
commit_scroll.grid(row=6, column=5, sticky=(tk.N, tk.S))
commit_text.config(yscrollcommand=commit_scroll.set)

commit_frame = tk.Frame(commit_text)

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
mainframe.columnconfigure(1, weight=1)
mainframe.columnconfigure(2, weight=1)
mainframe.columnconfigure(3, weight=1)
mainframe.columnconfigure(4, weight=1)

def on_closing():
    if commit_text:
        save_commit_text_and_exit(commit_text)
    else:
        root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Check if there is a saved file from the previous session and restore the content
if os.path.isfile("previous_session.txt"):
    with open("previous_session.txt", "r") as file:
        text_content = file.read()
        commit_text.insert(tk.END, text_content)

root.mainloop()