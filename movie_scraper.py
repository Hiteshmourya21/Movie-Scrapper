import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from urllib.parse import quote
import json
import random
from datetime import datetime, timedelta
import google.generativeai as genai

class AIReviewGenerator:
    def __init__(self):
        self.api_key = None
        self.model = None
        
    def set_api_key(self, api_key):
        """Set the Gemini API key"""
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            self.api_key = api_key
            return True
        except Exception as e:
            print(f"Error setting API key: {e}")
            return False
    
    def generate_reviews(self, movie_title, num_reviews=50):
        """Generate realistic movie reviews using Gemini"""
        if not self.model:
            return [], "API key not configured"
            
        try:
            prompt = f"""Generate {num_reviews} realistic and diverse movie reviews for "{movie_title}". 
            
            Make the reviews varied in:
            - Opinion (mix of positive, negative, and neutral)
            - Length (some short, some detailed)
            - Writing style (casual, formal, emotional, analytical)
            - Focus areas (acting, plot, cinematography, effects, music, etc.)
            
            For each review, provide:
            1. A rating from 1-10
            2. A brief title/summary (5-10 words)
            3. The full review text (50-300 words)
            4. A realistic username
            5. A recent date (within last 6 months)
            
            Format as JSON array with this structure:
            [
                {{
                    "rating": "8/10",
                    "title": "Great performances and stunning visuals",
                    "content": "Full review text here...",
                    "author": "MovieFan2024",
                    "date": "15 January 2024"
                }}
            ]
            
            Make sure reviews feel authentic and include specific details that real viewers would mention."""
            
            response = self.model.generate_content(prompt)
            
            # Try to parse JSON from response
            try:
                # Extract JSON from the response text
                text = response.text
                
                # Find JSON array in the response
                start_idx = text.find('[')
                end_idx = text.rfind(']') + 1
                
                if start_idx != -1 and end_idx != -1:
                    json_text = text[start_idx:end_idx]
                    reviews_data = json.loads(json_text)
                    return reviews_data, None
                else:
                    # If no JSON found, create reviews from text
                    return self._parse_text_reviews(text, num_reviews), None
                    
            except json.JSONDecodeError:
                # Fallback: parse the text manually
                return self._parse_text_reviews(response.text, num_reviews), None
                
        except Exception as e:
            return [], f"AI generation error: {str(e)}"
    
    def _parse_text_reviews(self, text, num_reviews):
        """Fallback method to parse reviews from text response"""
        reviews = []
        
        # Split text into potential review sections
        sections = re.split(r'\n\s*\n', text)
        
        for i, section in enumerate(sections[:num_reviews]):
            if len(section.strip()) < 20:  # Skip very short sections
                continue
                
            # Extract rating if present
            rating_match = re.search(r'(\d+(?:\.\d+)?/10|\d+/5|\d+ stars?)', section)
            rating = rating_match.group(1) if rating_match else f"{random.randint(4, 9)}/10"
            
            # Generate other fields
            title = f"AI Generated Review {i+1}"
            content = section.strip()[:500]  # Limit content length
            author = f"AIReviewer{random.randint(100, 999)}"
            
            # Generate random recent date
            days_ago = random.randint(1, 180)
            date = (datetime.now() - timedelta(days=days_ago)).strftime("%d %B %Y")
            
            reviews.append({
                'rating': rating,
                'title': title,
                'content': content,
                'author': author,
                'date': date
            })
        
        return reviews

class MovieReviewScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def search_movie(self, movie_title):
        """Search for movie and return IMDb ID"""
        try:
            search_query = quote(movie_title)
            search_url = f"https://www.imdb.com/find/?q={search_query}&s=tt&ttype=ft"
            
            response = self.session.get(search_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for movie links
            movie_links = soup.find_all('a', href=re.compile(r'/title/tt\d+/'))
            
            if movie_links:
                href = movie_links[0]['href']
                movie_id = re.search(r'tt\d+', href).group()
                return movie_id, None
            else:
                return None, "Movie not found"
                
        except Exception as e:
            return None, f"Search error: {str(e)}"

    def get_reviews(self, movie_id, max_reviews=50):
        """Extract reviews from IMDb"""
        try:
            reviews = []
            review_url = f"https://www.imdb.com/title/{movie_id}/reviews"
            
            response = self.session.get(review_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find review containers
            review_containers = soup.find_all('div', class_='review-container')
            
            for container in review_containers[:max_reviews]:
                try:
                    # Extract rating
                    rating_elem = container.find('span', class_='rating-other-user-rating')
                    rating = rating_elem.find('span').text if rating_elem else "No rating"
                    
                    # Extract title
                    title_elem = container.find('a', class_='title')
                    title = title_elem.text.strip() if title_elem else "No title"
                    
                    # Extract review text
                    content_elem = container.find('div', class_='text')
                    if content_elem:
                        content = content_elem.text.strip()
                    else:
                        content = "No content available"
                    
                    # Extract date
                    date_elem = container.find('span', class_='review-date')
                    date = date_elem.text.strip() if date_elem else "No date"
                    
                    # Extract author
                    author_elem = container.find('span', class_='display-name-link')
                    author = author_elem.text.strip() if author_elem else "Anonymous"
                    
                    review = {
                        'rating': rating,
                        'title': title,
                        'content': content,
                        'date': date,
                        'author': author
                    }
                    
                    reviews.append(review)
                    
                except Exception as e:
                    print(f"Error parsing review: {e}")
                    continue
            
            return reviews, None if reviews else "No reviews found"
            
        except Exception as e:
            return [], f"Error fetching reviews: {str(e)}"

class MovieReviewApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 AI-Powered Movie Review Generator")
        self.root.geometry("1000x800")
        self.root.configure(bg='#f0f0f0')
        
        self.scraper = MovieReviewScraper()
        self.ai_generator = AIReviewGenerator()
        self.reviews = []
        self.current_movie = ""
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="🎬 AI-Powered Movie Review Generator", 
                              font=("Arial", 18, "bold"), bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=(0, 20))
        
        # API Key frame
        api_frame = tk.LabelFrame(main_frame, text="🔑 Gemini API Configuration", 
                                 font=("Arial", 10, "bold"), bg='#f0f0f0')
        api_frame.pack(fill=tk.X, pady=(0, 10))
        
        api_input_frame = tk.Frame(api_frame, bg='#f0f0f0')
        api_input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(api_input_frame, text="API Key:", font=("Arial", 10), bg='#f0f0f0').pack(side=tk.LEFT)
        
        self.api_key_entry = tk.Entry(api_input_frame, show="*", width=50, font=("Arial", 10))
        self.api_key_entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        self.set_api_btn = tk.Button(api_input_frame, text="Set API Key", 
                                   command=self.set_api_key, bg='#3498db', 
                                   fg='white', font=("Arial", 9, "bold"))
        self.set_api_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # API status
        self.api_status = tk.Label(api_frame, text="❌ API Key not configured", 
                                 font=("Arial", 9), bg='#f0f0f0', fg='#e74c3c')
        self.api_status.pack(pady=(0, 10))
        
        # Search frame
        search_frame = tk.LabelFrame(main_frame, text="🔍 Movie Search", 
                                   font=("Arial", 10, "bold"), bg='#f0f0f0')
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        search_input_frame = tk.Frame(search_frame, bg='#f0f0f0')
        search_input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(search_input_frame, text="Movie Name:", 
                font=("Arial", 10), bg='#f0f0f0').pack(side=tk.LEFT)
        
        self.entry = tk.Entry(search_input_frame, width=40, font=("Arial", 12))
        self.entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        self.entry.bind('<Return>', lambda e: self.start_process())
        
        # Options frame
        options_frame = tk.Frame(search_frame, bg='#f0f0f0')
        options_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(options_frame, text="Max Reviews:", 
                font=("Arial", 10), bg='#f0f0f0').pack(side=tk.LEFT)
        
        self.max_reviews_var = tk.StringVar(value="50")
        max_reviews_spinbox = tk.Spinbox(options_frame, from_=10, to=200, 
                                       textvariable=self.max_reviews_var, 
                                       width=10, font=("Arial", 10))
        max_reviews_spinbox.pack(side=tk.LEFT, padx=(5, 15))
        
        # Mode selection
        tk.Label(options_frame, text="Mode:", font=("Arial", 10), bg='#f0f0f0').pack(side=tk.LEFT)
        
        self.mode_var = tk.StringVar(value="ai_only")
        
        mode_frame = tk.Frame(options_frame, bg='#f0f0f0')
        mode_frame.pack(side=tk.LEFT, padx=(5, 0))
        
        tk.Radiobutton(mode_frame, text="AI Generated", variable=self.mode_var, 
                      value="ai_only", bg='#f0f0f0', font=("Arial", 9)).pack(side=tk.LEFT)
        tk.Radiobutton(mode_frame, text="Scrape + AI Fallback", variable=self.mode_var, 
                      value="scrape_fallback", bg='#f0f0f0', font=("Arial", 9)).pack(side=tk.LEFT)
        tk.Radiobutton(mode_frame, text="Scrape Only", variable=self.mode_var, 
                      value="scrape_only", bg='#f0f0f0', font=("Arial", 9)).pack(side=tk.LEFT)
        
        # Action buttons
        button_frame = tk.Frame(search_frame, bg='#f0f0f0')
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.generate_btn = tk.Button(button_frame, text="🚀 Generate Reviews", 
                                    command=self.start_process, bg='#27ae60', 
                                    fg='white', font=("Arial", 11, "bold"))
        self.generate_btn.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, 10))
        
        # Status label
        self.status_label = tk.Label(main_frame, text="Ready to generate reviews...", 
                                   font=("Arial", 10), bg='#f0f0f0', fg='#7f8c8d')
        self.status_label.pack(anchor=tk.W)
        
        # Results frame
        results_frame = tk.LabelFrame(main_frame, text="📊 Generated Reviews", 
                                    font=("Arial", 10, "bold"), bg='#f0f0f0')
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Treeview for reviews
        tree_frame = tk.Frame(results_frame, bg='#f0f0f0')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ('Rating', 'Title', 'Author', 'Date')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        self.tree.heading('Rating', text='Rating')
        self.tree.heading('Title', text='Review Title')
        self.tree.heading('Author', text='Author')
        self.tree.heading('Date', text='Date')
        
        self.tree.column('Rating', width=80, anchor=tk.CENTER)
        self.tree.column('Title', width=350)
        self.tree.column('Author', width=150)
        self.tree.column('Date', width=120, anchor=tk.CENTER)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click to show full review
        self.tree.bind('<Double-1>', self.show_full_review)
        
        # Export frame
        export_frame = tk.Frame(main_frame, bg='#f0f0f0')
        export_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.export_txt_btn = tk.Button(export_frame, text="📄 Export as TXT", 
                                      command=self.export_txt, bg='#27ae60', 
                                      fg='white', font=("Arial", 10, "bold"))
        self.export_txt_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.export_csv_btn = tk.Button(export_frame, text="📊 Export as CSV", 
                                      command=self.export_csv, bg='#e74c3c', 
                                      fg='white', font=("Arial", 10, "bold"))
        self.export_csv_btn.pack(side=tk.LEFT, padx=5)
        
        self.export_json_btn = tk.Button(export_frame, text="📋 Export as JSON", 
                                       command=self.export_json, bg='#9b59b6', 
                                       fg='white', font=("Arial", 10, "bold"))
        self.export_json_btn.pack(side=tk.LEFT, padx=5)
        
        # Stats label
        self.stats_label = tk.Label(export_frame, text="No reviews generated", 
                                  font=("Arial", 10), bg='#f0f0f0', fg='#7f8c8d')
        self.stats_label.pack(side=tk.RIGHT)
        
    def set_api_key(self):
        """Set the Gemini API key"""
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter your Gemini API key")
            return
            
        if self.ai_generator.set_api_key(api_key):
            self.api_status.config(text="✅ API Key configured successfully", fg='#27ae60')
            messagebox.showinfo("Success", "API key configured successfully!")
        else:
            self.api_status.config(text="❌ Invalid API key", fg='#e74c3c')
            messagebox.showerror("Error", "Failed to configure API key. Please check your key.")
    
    def start_process(self):
        movie_name = self.entry.get().strip()
        if not movie_name:
            messagebox.showerror("Input Error", "Please enter a movie name.")
            return
            
        mode = self.mode_var.get()
        
        if mode in ["ai_only", "scrape_fallback"] and not self.ai_generator.api_key:
            messagebox.showerror("API Error", "Please configure your Gemini API key first.")
            return
            
        self.generate_btn.config(state='disabled')
        thread = threading.Thread(target=self.process_reviews, args=(movie_name, mode))
        thread.daemon = True
        thread.start()
        
    def process_reviews(self, movie_name, mode):
        try:
            # Clear previous results
            self.tree.delete(*self.tree.get_children())
            self.reviews = []
            self.current_movie = movie_name
            
            # Update status
            self.root.after(0, self.progress.start)
            max_reviews = int(self.max_reviews_var.get())
            
            if mode == "ai_only":
                # Generate reviews using AI only
                self.root.after(0, lambda: self.status_label.config(
                    text=f"🤖 Generating {max_reviews} AI reviews for '{movie_name}'..."))
                
                reviews, error = self.ai_generator.generate_reviews(movie_name, max_reviews)
                
                if error:
                    self.root.after(0, lambda: self.show_error(error))
                    return
                    
                self.reviews = reviews
                self.root.after(0, lambda: self.status_label.config(
                    text=f"✅ Generated {len(reviews)} AI reviews for '{movie_name}'"))
                
            elif mode == "scrape_fallback":
                # Try scraping first, fallback to AI
                self.root.after(0, lambda: self.status_label.config(
                    text=f"🔍 Searching for '{movie_name}' on IMDb..."))
                
                movie_id, error = self.scraper.search_movie(movie_name)
                
                if not error:
                    self.root.after(0, lambda: self.status_label.config(
                        text=f"📖 Scraping reviews from IMDb..."))
                    
                    reviews, scrape_error = self.scraper.get_reviews(movie_id, max_reviews)
                    
                    if not scrape_error and reviews:
                        self.reviews = reviews
                        self.root.after(0, lambda: self.status_label.config(
                            text=f"✅ Scraped {len(reviews)} reviews from IMDb"))
                    else:
                        # Fallback to AI
                        self.root.after(0, lambda: self.status_label.config(
                            text=f"🤖 Scraping failed, generating AI reviews..."))
                        
                        ai_reviews, ai_error = self.ai_generator.generate_reviews(movie_name, max_reviews)
                        
                        if ai_error:
                            self.root.after(0, lambda: self.show_error(ai_error))
                            return
                            
                        self.reviews = ai_reviews
                        self.root.after(0, lambda: self.status_label.config(
                            text=f"✅ Generated {len(ai_reviews)} AI reviews (scraping failed)"))
                else:
                    # Fallback to AI
                    self.root.after(0, lambda: self.status_label.config(
                        text=f"🤖 Movie not found on IMDb, generating AI reviews..."))
                    
                    ai_reviews, ai_error = self.ai_generator.generate_reviews(movie_name, max_reviews)
                    
                    if ai_error:
                        self.root.after(0, lambda: self.show_error(ai_error))
                        return
                        
                    self.reviews = ai_reviews
                    self.root.after(0, lambda: self.status_label.config(
                        text=f"✅ Generated {len(ai_reviews)} AI reviews"))
                
            elif mode == "scrape_only":
                # Scrape only mode
                self.root.after(0, lambda: self.status_label.config(
                    text=f"🔍 Searching for '{movie_name}' on IMDb..."))
                
                movie_id, error = self.scraper.search_movie(movie_name)
                if error:
                    self.root.after(0, lambda: self.show_error(error))
                    return
                    
                self.root.after(0, lambda: self.status_label.config(
                    text=f"📖 Scraping reviews from IMDb..."))
                
                reviews, error = self.scraper.get_reviews(movie_id, max_reviews)
                
                if error:
                    self.root.after(0, lambda: self.show_error(error))
                    return
                    
                self.reviews = reviews
                self.root.after(0, lambda: self.status_label.config(
                    text=f"✅ Scraped {len(reviews)} reviews from IMDb"))
            
            # Update UI
            self.root.after(0, self.populate_reviews)
            
        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"Unexpected error: {str(e)}"))
        finally:
            self.root.after(0, self.progress.stop)
            self.root.after(0, lambda: self.generate_btn.config(state='normal'))
            
    def populate_reviews(self):
        """Populate the treeview with reviews"""
        for i, review in enumerate(self.reviews):
            # Truncate title for display
            title = review['title'][:60] + "..." if len(review['title']) > 60 else review['title']
            
            self.tree.insert('', 'end', values=(
                review['rating'],
                title,
                review['author'],
                review['date']
            ))
        
        # Update stats
        total = len(self.reviews)
        with_rating = sum(1 for r in self.reviews if r['rating'] != "No rating")
        avg_rating = self._calculate_average_rating()
        
        stats_text = f"Total: {total} reviews | {with_rating} with ratings"
        if avg_rating:
            stats_text += f" | Avg: {avg_rating:.1f}/10"
            
        self.stats_label.config(text=stats_text)
        
    def _calculate_average_rating(self):
        """Calculate average rating from reviews"""
        ratings = []
        for review in self.reviews:
            rating_text = review['rating']
            # Extract numeric rating
            match = re.search(r'(\d+\.?\d*)', rating_text)
            if match:
                try:
                    rating = float(match.group(1))
                    # Convert to 10-point scale if needed
                    if '/5' in rating_text or 'stars' in rating_text.lower():
                        rating = rating * 2
                    elif rating <= 5:  # Assume it's on 5-point scale
                        rating = rating * 2
                    ratings.append(min(rating, 10))  # Cap at 10
                except ValueError:
                    continue
        
        return sum(ratings) / len(ratings) if ratings else None
        
    def show_full_review(self, event):
        """Show full review in a new window"""
        selection = self.tree.selection()
        if not selection:
            return
            
        item = self.tree.item(selection[0])
        index = self.tree.index(selection[0])
        
        if index < len(self.reviews):
            review = self.reviews[index]
            
            # Create new window
            review_window = tk.Toplevel(self.root)
            review_window.title(f"Review by {review['author']}")
            review_window.geometry("700x600")
            review_window.configure(bg='#f0f0f0')
            
            # Review details
            details_frame = tk.Frame(review_window, bg='#f0f0f0')
            details_frame.pack(fill=tk.X, padx=15, pady=15)
            
            tk.Label(details_frame, text=f"⭐ Rating: {review['rating']}", 
                    font=("Arial", 14, "bold"), bg='#f0f0f0', fg='#e74c3c').pack(anchor=tk.W)
            tk.Label(details_frame, text=f"👤 Author: {review['author']}", 
                    font=("Arial", 11), bg='#f0f0f0').pack(anchor=tk.W, pady=(5, 0))
            tk.Label(details_frame, text=f"📅 Date: {review['date']}", 
                    font=("Arial", 11), bg='#f0f0f0').pack(anchor=tk.W)
            
            # Title
            title_frame = tk.Frame(review_window, bg='#f0f0f0')
            title_frame.pack(fill=tk.X, padx=15, pady=(10, 0))
            
            title_label = tk.Label(title_frame, text=f"📝 {review['title']}", 
                                 font=("Arial", 13, "bold"), wraplength=650, 
                                 bg='#f0f0f0', fg='#2c3e50')
            title_label.pack(anchor=tk.W)
            
            # Review content
            text_frame = tk.Frame(review_window, bg='#f0f0f0')
            text_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Arial", 11), 
                                bg='white', fg='#2c3e50', padx=10, pady=10)
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            text_widget.insert('1.0', review['content'])
            text_widget.config(state='disabled')
            
    def show_error(self, error_msg):
        """Show error message"""
        messagebox.showerror("Error", error_msg)
        self.status_label.config(text=f"❌ Error: {error_msg}")
        
    def export_txt(self):
        if not self.reviews:
            messagebox.showwarning("No Data", "No reviews to export.")
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save reviews as TXT"
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(f"Movie Reviews for: {self.current_movie}\n")
                    file.write("=" * 50 + "\n\n")
                    
                    for i, review in enumerate(self.reviews, 1):
                        file.write(f"Review #{i}\n")
                        file.write(f"Rating: {review['rating']}\n")
                        file.write(f"Title: {review['title']}\n")
                        file.write(f"Author: {review['author']}\n")
                        file.write(f"Date: {review['date']}\n")
                        file.write(f"Content:\n{review['content']}\n")
                        file.write("-" * 30 + "\n\n")
                        
                messagebox.showinfo("Export Successful", f"Reviews exported to {filepath}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
                
    def export_csv(self):
        if not self.reviews:
            messagebox.showwarning("No Data", "No reviews to export.")
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save reviews as CSV"
        )
        
        if filepath:
            try:
                df = pd.DataFrame(self.reviews)
                df.to_csv(filepath, index=False, encoding='utf-8')
                messagebox.showinfo("Export Successful", f"Reviews exported to {filepath}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
                
    def export_json(self):
        if not self.reviews:
            messagebox.showwarning("No Data", "No reviews to export.")
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save reviews as JSON"
        )
        
        if filepath:
            try:
                data = {
                    'movie': self.current_movie,
                    'total_reviews': len(self.reviews),
                    'reviews': self.reviews
                }
                
                with open(filepath, 'w', encoding='utf-8') as file:
                    json.dump(data, file, indent=2, ensure_ascii=False)
                    
                messagebox.showinfo("Export Successful", f"Reviews exported to {filepath}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

def main():
    root = tk.Tk()
    app = MovieReviewApp(root)
    
    # Center the window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()