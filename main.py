import tkinter as tk
from tkinter import ttk, messagebox
import threading
from scraper import get_imdb_reviews
from utils import export_to_txt, export_to_csv
from dummy_reviews import dummy_reviews


class MovieReviewApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Movie Review Scraper")
        self.root.geometry("700x500")

        self.label = tk.Label(root, text="Enter Movie Name:", font=("Arial", 12))
        self.label.pack(pady=10)

        self.entry = tk.Entry(root, width=50, font=("Arial", 12))
        self.entry.pack(pady=5)

        self.search_button = tk.Button(root, text="Fetch Reviews", command=self.start_scraping)
        self.search_button.pack(pady=10)

        self.text = tk.Text(root, wrap=tk.WORD, font=("Arial", 10))
        self.text.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)

        self.export_txt = tk.Button(root, text="Export as TXT", command=lambda: export_to_txt(self.reviews))
        self.export_txt.pack(side=tk.LEFT, padx=20, pady=10)

        self.export_csv = tk.Button(root, text="Export as CSV", command=lambda: export_to_csv(self.reviews))
        self.export_csv.pack(side=tk.RIGHT, padx=20, pady=10)

        self.progress = ttk.Progressbar(root, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=20, pady=5)
        
        self.reviews = []

    def start_scraping(self):
        thread = threading.Thread(target=self.scrape_reviews)
        thread.start()

    def scrape_reviews(self):
        self.text.delete(1.0, tk.END)
        movie_name = self.entry.get().strip()
        if not movie_name:
            messagebox.showerror("Input Error", "Please enter a movie name.")
            return

        self.progress.start()
        self.reviews, error = get_imdb_reviews(movie_name)
        self.progress.stop()

        if error or not self.reviews:
            messagebox.showwarning("Fallback", "Could not fetch reviews. Displaying dummy reviews instead.")
            self.reviews = dummy_reviews

        for review in self.reviews:
            self.text.insert(tk.END, review + "\n\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = MovieReviewApp(root)
    root.mainloop()
