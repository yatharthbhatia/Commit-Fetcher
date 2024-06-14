import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import font as tkfont
from tkcalendar import DateEntry
import webbrowser
import csv
import pytz
from datetime import datetime
import os
from tkinter import Scrollbar
import json

load_dotenv()

GITHUB_TOKEN = ""

def show_progress_bar():
    global overlay_frame
    global progress_bar

    overlay_frame = tk.Toplevel(root)
    overlay_frame.attributes('-alpha', 0.5)
    overlay_frame.configure(bg='black')
    overlay_frame.overrideredirect(True) 
    overlay_frame.geometry(f"{root.winfo_width()}x{root.winfo_height()}+{root.winfo_x()}+{root.winfo_y()}")

    progress_bar = ttk.Progressbar(overlay_frame, mode='indeterminate', style='CircleStyle.Horizontal.TProgressbar')
    progress_bar.pack(padx=100, pady=50)

    progress_bar.start()

    return overlay_frame, progress_bar


def destroy_progress_bar():
    global overlay_frame
    global progress_bar

    if progress_bar:
        progress_bar.stop()
        progress_bar.destroy()
        progress_bar = None

    if overlay_frame:
        overlay_frame.destroy()
        overlay_frame = None


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

    global GITHUB_TOKEN

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
    
    global overlay_frame
    global progress_bar

    overlay_frame, progress_bar = show_progress_bar()


    global commits
    commits = fetch_commits(repo_url, branch, since, until)
    
    if commits:
        commit_text.config(state=tk.NORMAL)
        commit_text.delete("1.0", tk.END)

        header = "Author".ljust(20) + "Date".ljust(30) + "Message".ljust(60) + "Files Changed".ljust(50) + \
                 "Status".ljust(15) + "Additions".ljust(10) + "Deletions".ljust(10) + "\n"
        commit_text.insert(tk.END, header)
        commit_text.insert(tk.END, "-" * 200 + "\n")

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
                file_info_list = []
                for file in commit_details['files']:
                    filename = file['filename']
                    additions = file['additions']
                    deletions = file['deletions']
                    status = file['status']
                    file_info_list.append(f"{filename} (A: {additions}, D: {deletions}, S: {status})")
                file_info = "; ".join(file_info_list)
                
                row = f"{author_name.ljust(20)}{commit_date_ist_str.ljust(25)}{commit_message.ljust(60)}" \
                      f"{file_info.ljust(90)}"
                
                commit_text.insert(tk.END, row + '\n')
        
        save_csv_button = ttk.Button(mainframe, text="Save to CSV", command=save_to_csv)
        save_csv_button.grid(row=7, column=2, sticky=tk.W)       
       
        commit_text.config(state=tk.DISABLED)

        destroy_progress_bar()        
        root.protocol("WM_DELETE_WINDOW", lambda: save_commit_text_and_exit(commit_text))
        save_preferences()

    else:
        destroy_progress_bar()
        messagebox.showerror("Error", "No commits fetched.")
        save_preferences()

def convert_api_commit_url_to_page_url(api_commit_url):
    # Check if the URL contains '/commits/' substring
    if '/commits/' in api_commit_url:
        # Replaces '/commits/' with '/commit/'
        page_commit_url = api_commit_url.replace('/commits/', '/commit/')
        return page_commit_url
    else:
        return api_commit_url

def save_to_csv():
    global commits

    if not commits:
        messagebox.showerror("Error", "No commits fetched. Please fetch commits first.")
        return
    
    global overlay_frame
    global progress_bar

    overlay_frame, progress_bar = show_progress_bar()

    with filedialog.asksaveasfile(mode='w', defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]) as csvfile:
        if csvfile is not None:
            fieldnames = []
            if author_var.get():
                fieldnames.append('Author')
            if date_var.get():
                fieldnames.append('Date')
            if message_var.get():
                fieldnames.append('Message')
            if filenames_var.get():
                fieldnames.append('Files Changed')
            if status_var.get():
                fieldnames.append('Status')
            if additions_var.get():
                fieldnames.append('Additions')
            if deletions_var.get():
                fieldnames.append('Deletions')
            if raw_urls_var.get():
                fieldnames.append('Raw URLs')
            if commit_url_var.get():
                fieldnames.append('Commit URL')

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for commit in commits:
                commit_message = commit['commit']['message']
                author_name = commit['commit']['author']['name']
                commit_date = commit['commit']['author']['date']

                commit_details = fetch_commit_details(commit['url'])
                if commit_details and 'files' in commit_details:
                    file_info_list = []
                    for file in commit_details['files']:
                        filename = file['filename']
                        additions = file['additions']
                        deletions = file['deletions']
                        status = file['status']
                        file_info_list.append(f"{filename} (A: {additions}, D: {deletions}, S: {status})")
                    files_changed = "; ".join(file_info_list)

                    commit_url = convert_api_commit_url_to_page_url(commit['html_url'])

                    row_data = {}
                    if 'Author' in fieldnames:
                        row_data['Author'] = author_name
                    if 'Date' in fieldnames:
                        row_data['Date'] = commit_date
                    if 'Message' in fieldnames:
                        row_data['Message'] = commit_message
                    if 'Files Changed' in fieldnames:
                        row_data['Files Changed'] = files_changed
                    if 'Status' in fieldnames:
                        row_data['Status'] = status
                    if 'Additions' in fieldnames:
                        row_data['Additions'] = additions
                    if 'Deletions' in fieldnames:
                        row_data['Deletions'] = deletions
                    if 'Raw URLs' in fieldnames:
                        row_data['Raw URLs'] = file['raw_url']
                    if 'Commit URL' in fieldnames:
                        row_data['Commit URL'] = commit_url

                    writer.writerow(row_data)
            
            destroy_progress_bar()
            messagebox.showinfo("Success", f"Data saved to {csvfile.name}")
            save_preferences()
        else:
            destroy_progress_bar()
            messagebox.showerror("Error", "File save operation canceled.")
            save_preferences()


def update_branches():
    global GITHUB_TOKEN
    
    GITHUB_TOKEN = token_entry.get()
    
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

style = ttk.Style()
style.layout('CircleStyle.Horizontal.TProgressbar',
             [('Horizontal.Progressbar.trough',
               {'children': [('Horizontal.Progressbar.pbar',
                               {'side': 'left', 'sticky': 'ns'})],
                'sticky': 'nswe'}),
              ('Horizontal.Progressbar.label', {'sticky': ''})])
style.configure('CircleStyle.Horizontal.TProgressbar', background='blue', thickness=20)

heading_font = tkfont.Font(family="Segoe UI", size=28, weight="bold")

heading_label = ttk.Label(mainframe, text="GITHUB COMMIT FETCHER", font=heading_font)
heading_label.grid(row=0, column=0, columnspan=4, pady=20)

token_label = ttk.Label(mainframe, text="GitHub Token:")
token_label.grid(row=1, column=1, sticky=tk.W)

show_token = tk.BooleanVar(value=False)

# Function to toggle visibility and update button text
def toggle_token_visibility():
    global show_token
    show_token = not show_token
    if show_token:
        token_entry.config(show="")
        show_hide_button.config(text="Hide")
    else:
        token_entry.config(show="*")
        show_hide_button.config(text="Show")

token_entry = ttk.Entry(mainframe, show="*")
token_entry.grid(row=1, column=2, sticky=(tk.W, tk.E))


show_hide_button = ttk.Button(mainframe, text="Show", command=toggle_token_visibility)
show_hide_button.grid(row=1, column=3, sticky=tk.W)

repo_url_label = ttk.Label(mainframe, text="GitHub Repository URL:")
repo_url_label.grid(row=2, column=1, sticky=tk.W)
repo_url_entry = ttk.Entry(mainframe, width=50)
repo_url_entry.grid(row=2, column=2, sticky=(tk.W, tk.E))

github_token = ""
repo_url = ""

def save_preferences():
    global github_token, repo_url
    preferences = {
        "github_token": token_entry.get(),
        "repo_url": repo_url_entry.get()
    }
    with open('preferences.json', 'w') as file:
        json.dump(preferences, file)

def load_preferences():
    global github_token, repo_url
    try:
        with open('preferences.json', 'r') as file:
            preferences = json.load(file)
            github_token = preferences.get("github_token", "")
            repo_url = preferences.get("repo_url", "")
        
            token_entry.delete(0, tk.END)
            token_entry.insert(0, github_token)
            repo_url_entry.delete(0, tk.END)
            repo_url_entry.insert(0, repo_url)

    except FileNotFoundError:
        print("Preferences file not found.")

load_preferences()

fetch_branches_button = ttk.Button(mainframe, text="Fetch Branches", command=update_branches, width=20, style='TButton')
fetch_branches_button.grid(row=2, column=3, sticky=tk.W)

branch_label = ttk.Label(mainframe, text="Branch:")
branch_label.grid(row=3, column=1, sticky=tk.W)
branch_combobox = ttk.Combobox(mainframe, state="readonly")
branch_combobox.grid(row=3, column=2, sticky=(tk.W, tk.E))

since_date_label = ttk.Label(mainframe, text="Start Date:")
since_date_label.grid(row=4, column=1, sticky=tk.W)
since_date_entry = DateEntry(mainframe, width=12, background='darkblue',
                             foreground='white', borderwidth=2, year=2024, date_pattern="dd-mm-yyyy")
since_date_entry.grid(row=4, column=2, sticky=(tk.W, tk.E))

until_date_label = ttk.Label(mainframe, text="End Date:")
until_date_label.grid(row=5, column=1, sticky=tk.W)
until_date_entry = DateEntry(mainframe, width=12, background='darkblue',
                             foreground='white', borderwidth=2, year=2024, date_pattern="dd-mm-yyyy")
until_date_entry.grid(row=5, column=2, sticky=(tk.W, tk.E))

fetch_button = ttk.Button(mainframe, text="Fetch Commits", command=display_commits, width=15, style='TButton')
fetch_button.grid(row=6, column=2, sticky=tk.W)

# commit_text = tk.Text(mainframe, wrap="word", width=180, height=40)
# commit_text.grid(row=6, column=1, columnspan=2, sticky=(tk.W, tk.E))

commit_frame = tk.Frame(mainframe)
commit_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))

commit_text = tk.Text(commit_frame, wrap="none", width=180, height=30)
commit_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Define BooleanVar variables for checkboxes
author_var = tk.BooleanVar()
date_var = tk.BooleanVar()
message_var = tk.BooleanVar()
filenames_var = tk.BooleanVar()
status_var = tk.BooleanVar()
additions_var = tk.BooleanVar()
deletions_var = tk.BooleanVar()
raw_urls_var = tk.BooleanVar()
commit_url_var = tk.BooleanVar()

csv_frame = ttk.LabelFrame(mainframe, text="CSV Export Options")
csv_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E))

ttk.Checkbutton(csv_frame, text="Author", variable=author_var).grid(row=0, column=0, sticky=tk.W)
ttk.Checkbutton(csv_frame, text="Date", variable=date_var).grid(row=0, column=1, sticky=tk.W)
ttk.Checkbutton(csv_frame, text="Message", variable=message_var).grid(row=0, column=2, sticky=tk.W)
ttk.Checkbutton(csv_frame, text="Files Changed", variable=filenames_var).grid(row=1, column=0, sticky=tk.W)
ttk.Checkbutton(csv_frame, text="Status", variable=status_var).grid(row=1, column=1, sticky=tk.W)
ttk.Checkbutton(csv_frame, text="Additions", variable=additions_var).grid(row=1, column=2, sticky=tk.W)
ttk.Checkbutton(csv_frame, text="Deletions", variable=deletions_var).grid(row=2, column=0, sticky=tk.W)
ttk.Checkbutton(csv_frame, text="Raw URLs", variable=raw_urls_var).grid(row=2, column=1, sticky=tk.W)
ttk.Checkbutton(csv_frame, text="Commit URL", variable=commit_url_var).grid(row=2, column=2, sticky=tk.W)


scroll_x = Scrollbar(commit_frame, orient=tk.HORIZONTAL, command=commit_text.xview)
commit_text.configure(xscrollcommand=scroll_x.set)
scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))

commit_text.config(state=tk.NORMAL)
commit_text.delete("1.0", tk.END)

commit_scroll = ttk.Scrollbar(mainframe, orient=tk.VERTICAL, command=commit_text.yview)
commit_scroll.grid(column=4, sticky=(tk.N, tk.S))
commit_text.config(yscrollcommand=commit_scroll.set)

commit_frame = tk.Frame(commit_text)

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
mainframe.columnconfigure(1, weight=1)
mainframe.columnconfigure(2, weight=1)
mainframe.columnconfigure(3, weight=1)
mainframe.columnconfigure(4, weight=1)

# Save the text content to a file when closing the application
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