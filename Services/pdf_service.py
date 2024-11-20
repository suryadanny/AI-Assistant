import numpy as np
from PyPDF2 import PdfReader
from Services.llm_service import LLMService
import tkinter as tk
from tkinter import filedialog

def _create_prompt(query):
    prompt = 'As a good assistant, give me an answer to the question - ' + query + '\n' \
            'consider the below transcript for your reference  - \n\n'
    return prompt


def open_file_dialog():
    # Initialize Tkinter root (won't show the root window)
    root = tk.Tk()
    root.withdraw()  # Hide the Tkinter root window

    # Open file dialog
    file_paths = filedialog.askopenfilenames(title="Select a files")
    print(f"File selected: {file_paths}")
    return file_paths


class PdfService(LLMService):
    def __init__(self,  model, url):
        #self.path = dirs
        #ThreadPoolTaskExecutor
        super().__init__()

    def extract_text(self, dir):
        reader = PdfReader(dir)
        text = "".join(page.extract_text() for page in reader.pages if page.extract_text())
        return text

    def find_answer(self, query):
        transcripts = []
        for path in open_file_dialog():
            transcripts.append(self.extract_text(path))

        prompt = _create_prompt(query)
        prompt += '\n'.join(transcripts)
        #print(prompt)
        try:
            answer = self.query_local(prompt)
            print('\n')
            print('As Extracted in PDF, or from LLM if related information not available - \n')
            print(answer)
        except Exception as ex:
            print(str(ex))

        return ''


