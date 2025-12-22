# Healer-AI

HealerAI is a AI assistant that streamlines the patient-doctor journey by automating scheduling, intake, documentation, and follow-up. Built with agentic AI, it goes beyond chatbots to capture patient history, generate structured reports, retrieve records, and provide reliable post-visit support all within an end-to-end deployable system.

**[Documentation](Docs.md)**

## Information

- Submitter Name: Aditya Kumar Puri
- GithubId : [puri-adityakumar](https://github.com/puri-adityakumar)
- LinkedIn : [puriadityakumar](https://www.linkedin.com/in/puriadityakumar/)

## Prerequisites

- **Python Environment**: Ensure you have Python installed (version 3.8+) to run the Jupyter notebook (`src/main.ipynb`) for API testing and development.
- **Supabase Account**: A Supabase account is required for the database and edge functions. **Note**: You don't need to create a new account as the repository already includes credentials for connecting to the database and the edge function is already hosted.
- **Langflow**: Install Langflow locally or use the cloud-based version at [https://www.datastax.com/](https://www.datastax.com/) for running the agentic workflow.
- **API Keys**: Obtain the following API keys for the workflow:
  - `WATSONX_API`: For IBM watsonx.ai models (conversation generation, embeddings, etc.).
  - `GEMINI_API`: For Google Generative AI models (appointment orchestration, RAG agent).
  - `ASTRA_DB_APPLICATION_TOKEN`: For AstraDB vector database operations (ingestion, search, retrieval).
  - `PROJECT_ID`: It's watsonx.ai project Id

## Installation Steps

1. **Set Up API Testing Notebook**:

   - Create a virtual environment: `python -m venv venv`
   - Activate the virtual environment: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (macOS/Linux)
   - Install dependencies: `pip install -r src/requirements.txt`
   - Open and execute the notebook: `src/main.ipynb` to test API endpoints.

2. **Set Up Langflow Workflow (Cloud-Based)**:
   - Log in to the Langflow dashboard on [DataStax](https://www.datastax.com/).
   - Import the workflow file: `src/workflow/workflow.json`.
   - Navigate to Settings > Global Variables.
   - Add the required API keys and variables from Prerequisites (WATSONX_API, GEMINI_API, ASTRA_DB_APPLICATION_TOKEN).
   - - You're all set to run the agentic workflow!

## Important Note

Please refer to the [Documentation](Docs.md) for detailed information and the Demo video below.

## Demo
