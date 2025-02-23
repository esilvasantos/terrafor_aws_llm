Database Query Assistant
Project Description

The Database Query Assistant is a web application that allows users to interact with PostgreSQL databases in an intuitive way, using natural language. The system combines a user-friendly interface with natural language processing (LLM) to convert natural language queries into valid SQL commands.

Main Features

Database Exploration
View schemas and tables
Intuitive navigation through the database structure
Statistical analysis of tables
Query Generation
Conversion of natural language to SQL
Query history
Formatted display of results
Data Analysis
Schema summary
Detailed table statistics
Visualization of relationships
Technologies Used

Backend: Python/Flask
Frontend: HTML5, CSS3, JavaScript
Database: PostgreSQL
LLM: Ollama - Llama 3.2
Libraries: psycopg2, pandas, numpy
Docker
Real-World Use Cases

Business Data Analysis
Rapid report generation
Exploratory data analysis
Metrics monitoring
Decision Support
Simplified ad-hoc queries
Trend analysis
Pattern identification
Educational
SQL learning
Exploration of data structures
Training in data analysis
Development and Debugging
Quick query testing
Structure validation
Performance analysis
Improvements


projet/
│
├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── database.py
│   ├── llm.py
│   └── templates/
│       └── index.html
│-- terraform
│    │-- main.tf
│    │-- terraform.tfstate
│
│
├── config.py
├── wsgi.py
└── requirements.txt


docker run --name llm_postgres \
  -p 5959:5432 \
  -p 11434:11434 \
  -p 5001:5001 \
  -v ./:/app \
  --env-file .env \
  -d llm-postgres



-- run 

nohup gunicorn -w 4 -b 0.0.0.0:5001 wsgi:app