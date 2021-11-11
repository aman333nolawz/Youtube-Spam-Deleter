import os
import pickle
import tkinter as tk
from tkinter import messagebox, ttk

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

root = tk.Tk()

root.tk.call("source", "Sun Valley Theme/sun-valley.tcl")
root.tk.call("set_theme", "dark")

credentials = None

ban_spammer = tk.IntVar()

next_page_token = "start"
scanned_comments = 0
scammer_comments = 0
max_scan_number = 1000

if os.path.exists("token.pickle"):
    print("Loading Credentials from file...")
    with open("token.pickle", "rb") as token:
        credentials = pickle.load(token)

if not credentials or not credentials.valid:
    if credentials and credentials.expired and credentials.refresh_token:
        print("Refreshing Access Token...")
        credentials.refresh(Request())
    else:
        print("Fetching New Tokens...")
        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json",
            scopes=["https://www.googleapis.com/auth/youtube.force-ssl"],
        )

        flow.run_local_server(port=8080, prompt="consent")
        credentials = flow.credentials

        # Save the credentials for the next run
        with open("token.pickle", "wb") as f:
            print("Saving Credentials for Future Use...")
            pickle.dump(credentials, f)


def delete_comments_from_user(
    video_ids, user_id, ban_choice=True, next_page_token=None
):
    global scanned_comments, scammer_comments
    youtube = build("youtube", "v3", credentials=credentials)
    for video_id in video_ids:
        results = (
            youtube.commentThreads()
            .list(
                part="snippet",
                videoId=video_id,
                maxResults=100,
                pageToken=next_page_token,
                fields="nextPageToken,items/snippet/topLevelComment/id,items/snippet/totalReplyCount,items/snippet/topLevelComment/snippet/authorChannelId/value,items/snippet/topLevelComment/snippet/videoId",
                textFormat="plainText",
            )
            .execute()
        )

        try:
            retrieved_next_page_token = results["nextPageToken"]
        except KeyError:
            retrieved_next_page_token = "end"

        items = results["items"]
        for item in items:
            comment = item["snippet"]["topLevelComment"]
            comment_channel = item["snippet"]["topLevelComment"]["snippet"][
                "authorChannelId"
            ]["value"]
            if comment_channel == user_id:
                comment_id = comment["id"]
                print(f"Deleting comment id: {comment_id}")
                request = youtube.comments().setModerationStatus(
                    id=comment_id, moderationStatus="rejected", banAuthor=ban_choice
                )
                res = request.execute()
                scammer_comments += 1
            scanned_comments += 1

    return retrieved_next_page_token


def delete_comments(*args):
    global next_page_token, max_scan_number

    entry = max_scan_entry.get()
    spammer_id = spammer_entry.get()
    video_id = video_entry.get()
    ban_choice = bool(ban_spammer.get())

    if not all((video_id, spammer_id, entry)):
        messagebox.showerror(
            "Required Fields can't be blank", "Please fill up the required fields"
        )
        return

    try:
        max_scan_number = int(entry)
        if max_scan_number < 0:
            messagebox.showerror(
                "Enter a number number greater than 0",
                "Please provide a number greater than 0 for the maximum scans field.",
            )
            return
    except ValueError:
        messagebox.showerror(
            "Enter a number for maximum scans",
            "Please provide a number for the maximum scans field.",
        )
        return

    try:
        if next_page_token == "start":
            next_page_token = delete_comments_from_user(
                [video_id], spammer_id, ban_choice=ban_choice
            )
        while next_page_token != "end" and scanned_comments < max_scan_number.get():
            next_page_token = delete_comments_from_user(
                [video_id], spammer_id, ban_choice=ban_choice
            )
        messagebox.showinfo(
            "Deleted spam comments",
            f"Deleted {scammer_comments} comments from the user id {spammer_id}",
        )
    except Exception as e:
        messagebox.showerror(
            "Some error occured", "Something went wrong", detail=f"Error:\n{e}"
        )


spammer_label = ttk.Label(root, text="Spammer's ID*")
spammer_entry = ttk.Entry(root)

video_label = ttk.Label(root, text="Video ID*")
video_entry = ttk.Entry(root)

max_scan_label = ttk.Label(root, text="Max. number of comments to scan*")
max_scan_entry = ttk.Entry(root)

ban_spammer_btn = ttk.Checkbutton(root, text="Ban User", variable=ban_spammer)

delete_btn = ttk.Button(
    root, text="Delete Comments", style="Accent.TButton", command=delete_comments
)

spammer_label.grid(row=0, column=0, padx=5, pady=(10, 5), sticky=tk.W)
spammer_entry.grid(row=0, column=1, padx=5, pady=(10, 5))

video_label.grid(row=1, column=0, padx=5, pady=(5, 10), sticky=tk.W)
video_entry.grid(row=1, column=1, padx=5, pady=(5, 10))

max_scan_label.grid(row=2, column=0, padx=5, pady=(5, 10), sticky=tk.W)
max_scan_entry.grid(row=2, column=1, padx=5, pady=(5, 10))


ban_spammer_btn.grid(row=3, column=1, pady=(5, 10), sticky=tk.W)

delete_btn.grid(row=4, column=0, columnspan=2)

root.mainloop()
