import pandas as pd
from tkinter import filedialog

def export_to_txt(reviews):
    filepath = filedialog.asksaveasfilename(defaultextension=".txt")
    if filepath:
        with open(filepath, 'w', encoding='utf-8') as file:
            for review in reviews:
                file.write(review + '\n\n')

def export_to_csv(reviews):
    filepath = filedialog.asksaveasfilename(defaultextension=".csv")
    if filepath:
        df = pd.DataFrame({'Review': reviews})
        df.to_csv(filepath, index=False)
