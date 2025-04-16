# RAG for Setting up the Network

This project implements a RAG-based Network Integration Assistant that helps users with network equipment integration across different vendors.

## Features

- Query analysis for network integration tasks
- Retrieval-augmented generation using a vector database
- Web search fallback for insufficient context
- Support for multiple vendors (Cisco, Juniper, Aruba, etc.)
- PDF and HTML document processing

## Components

- FastAPI backend
- Vector store using ChromaDB
- LLM service (currently using DeepSeek, with plans to support Groq)
- Web scraper for documentation ingestion
- Document processor for chunking and metadata extraction

## Setup

1. Clone the repository with `git clone https://github.com/A-m-i-t-M/HPE-CPP.git`
2. Create a virtual environment `python -m venv venv` & activate it.
   - Windows: `venv\Scripts\activate`
   - Linux/Mac : `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Set up environment variables (see `environment.py`)
   - Add `GROQ_API_KEY` to your environment variables
   - Set `GROQ_MODEL` (default: "deepseek-r1-distill-llama-70b")
5. Run the application: `python main.py`
6. Run the streamlit app: `streamlit gui.py`

## Usage

The main entry point is `main.py`. It initializes components and starts the FastAPI server.  
For the initial run, kindly enter 'y' for all the user prompts. Note: The scraping of the Aruba PDFs takes some time.  
The streamlit app is a provision for the users to enter their prompts. `streamlit run gui.py`  
Blast away with your queries!

