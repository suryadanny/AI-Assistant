# Personal AI Assistant: Architecture and Features

This project implements a modular **Personal Assistant System** capable of handling a variety of tasks such as email management, meeting scheduling, PDF document parsing, and web search functionality. It is designed with a service-oriented architecture, ensuring that each component specializes in specific operations while collaborating seamlessly.

---


## Getting Started

### Prerequisites
- Python 3.x
- Required Libraries: `PyPDF2`, `jproperties`, `requests`, and others listed in `requirements.txt`.

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/personal-assistant-system.git

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   
3. Set up API credentials for Gmail, Google Calendar, Brave API, and the language model.

### Usage

Run the main script with appropriate commands:


### Overview

The system consists of:
- A **Main Script** that serves as the entry point, routing user inputs to the appropriate services.
- **Service Modules** that handle domain-specific tasks like email and calendar management, PDF processing, and web search.
- A **Language Model Integration** to process natural language queries and classify commands.
  
## Architecture Components

### 1. **Core Components**
- **Main Script (`main()`)**: 
  - Entry point for the application.
  - Parses command-line inputs to determine the appropriate service to execute.
  
- **LLMService**:
  - Connects to an external language model (e.g., `llama3-8b-8192`).
  - Interprets and classifies user inputs.
  - Provides utilities for identifying whether a query involves personal or public data.

---

### 2. **Service Modules**
- **GSuiteService**:
  - A subclass of `LLMService` for handling email and calendar-related tasks.
  - Integrates with Gmail API for:
    - Sending, replying to, and reading emails.
  - Utilizes Google Calendar API for:
    - Scheduling meetings, parsing attendee information, and creating events.
  - Includes logic to determine if emails require responses.

- **PdfService**:
  - Extracts text from PDF documents using `PyPDF2`.
  - Processes text with the language model for:
    - Summarizing content.
    - Answering user queries based on document information.

- **SearchService**:
  - Performs web searches using the Brave API.
  - Retrieves and summarizes results efficiently with multithreading.

- **Groq Client**:
  - Integrated within `LLMService` for interacting with the external language model API.
  - Generates:
    - Email subjects and body text.
    - Meeting scheduling prompts.

---

### 3. **Utilities and Configurations**
- **Configuration Management**:
  - Uses the `jproperties` library to store and retrieve settings like model URLs and API keys.

- **Authentication**:
  - GSuiteService uses OAuth 2.0 for authenticating with Google APIs.
  - Credentials are managed using `token.json` or `client_secret.json`.

---

## Key Functionalities

### Command Parsing
- Parses commands to determine the required task.
  - Example: Commands with "email" activate `GSuiteService`, while "PDF" invokes `PdfService`.

### Email Management
- Automates sending and replying to emails.
- Generates context-aware email content using the language model.

### Meeting Scheduling
- Extracts details such as date, time, and attendees from commands.
- Creates Google Calendar events with Google Meet links.

### PDF Parsing and QA
- Extracts and analyzes text from PDFs.
- Provides document summaries and answers queries based on the content.

### Web Search and Summarization
- Conducts web queries via the Brave API.
- Retrieves, processes, and summarizes search results efficiently using multithreading.

---
