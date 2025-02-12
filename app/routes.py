import time
from flask import request, jsonify, render_template
from app import app
from app.database import Database
from app.llm import LLM
import logging
import numpy as np 

query_history = []

@app.route('/schemas', methods=['GET'])
def get_schemas():
    query = "SELECT schema_name FROM information_schema.schemata ORDER BY schema_name;"
    result = Database.query_database(query)
    
    if isinstance(result, tuple):
        df, formatted_output = result
        return jsonify({
            'schemas': df.to_dict(orient='records'),
            'formatted_output': formatted_output
        })
    else:
        return jsonify({'error': str(result)})

@app.route('/tables/<schema>', methods=['GET'])
def get_tables(schema):
    query = f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{schema}' ORDER BY table_name;"
    result = Database.query_database(query)
    
    if isinstance(result, tuple):
        df, formatted_output = result
        return jsonify({
            'tables': df.to_dict(orient='records'),
            'formatted_output': formatted_output
        })
    else:
        return jsonify({'error': str(result)})

@app.route('/set_schema', methods=['POST'])
def set_schema():
    schema = request.json.get('schema', '')
    if schema:
        return jsonify({"message": f"Schema set to {schema}"})
    else:
        return jsonify({"error": "Invalid schema"}), 400

@app.route('/query', methods=['POST'])
def generate_query():
    global query_history
    try:
        user_input = request.json.get('user_input', '')
        logging.debug(f"User input: {user_input}")

        prompt = f"""
        You are a PostgreSQL expert assistant.
        Convert the following request into a valid SQL query:
        '{user_input}'.
        Return ONLY the SQL query, with no explanations. If the request cannot be translated to SQL, return "INVALID QUERY".
        """

        sql_query = LLM.ask_ollama(prompt).strip().replace("sql", "").replace("", "")
        logging.debug(f"Generated SQL Query: {sql_query}")

        if sql_query.upper() == "INVALID QUERY":
            return jsonify({
                "query": sql_query,
                "history": query_history,
                "result_html": "<div class='alert alert-warning'>Invalid query request</div>"
            })

        result = Database.query_database(sql_query)
        query_history.insert(0, user_input)
        query_history = query_history[:10]

        if isinstance(result, tuple):
            df, formatted_output = result
            result_html = f"<pre class='query-result'>{formatted_output}</pre>"
            result_json = df.replace({np.nan: None}).to_dict(orient='records')
        else:
            result_html = f"<pre class='query-result'>{str(result)}</pre>"
            result_json = str(result)

        response_data = {
            "query": sql_query,
            "history": query_history,
            "result": result_json,
            "result_html": result_html
        }
        
        logging.debug(f"Response data: {response_data}")
        return jsonify(response_data)

    except Exception as e:
        logging.error(f"Error in generate_query: {str(e)}")
        return jsonify({
            "error": str(e),
            "query": "",
            "history": query_history,
            "result_html": f"<div class='alert alert-danger'>Error: {str(e)}</div>"
        }), 500

@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        data = request.get_json()
        schema = data['schema']
        schema_info = Database.get_schema_info(schema)
        summary = generate_schema_summary(schema_info)
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/analyze', methods=['POST'])
def analyze_table():
    try:
        data = request.get_json()
        schema = data.get('schema')
        table = data.get('table')
        
        if not schema or not table:
            return jsonify({
                'error': 'Schema and table names are required',
                'formatted_output': 'Schema and table names are required'
            }), 400
        
        stats, formatted_output = Database.get_table_statistics(schema, table)
        
        # Garantir que a saída formatada seja uma string
        if not isinstance(formatted_output, str):
            formatted_output = str(formatted_output)
            
        logging.debug(f"Analysis results: {formatted_output}")
        
        return jsonify({
            'raw_statistics': stats,
            'formatted_output': formatted_output
        })
    except Exception as e:
        logging.error(f"Error in analyze_table: {str(e)}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'error': str(e),
            'formatted_output': f"Error analyzing table: {str(e)}"
        }), 500

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

def generate_schema_summary(schema_info):
    start_time = time.time()
    
    schema_details = []
    for info in schema_info:
        schema_details.append(
            f"Table: {info[0]}\n"
            f"  Column: {info[1]}\n"
            f"  Type: {info[2]}\n"
            f"  Default: {info[3]}\n"
            f"  Nullable: {info[4]}\n"
        )
    
    schema_str = "\n".join(schema_details)
    
    prompt = f"""
    Analyze this database schema and provide a comprehensive summary.
    Format the output exactly as follows, with clear sections:
    
    1. Total Number of Tables
    2. Key Tables and Their Purposes
    3. Important Relationships Between Tables
    4. Notable Data Types Used
    5. Potential Design Patterns Observed
    6. Additional Observations
    
    Schema details:
    {schema_str}
    """
    
    response = LLM.ask_ollama(prompt)
    execution_time = time.time() - start_time
    
    formatted_output = [
        "SCHEMA SUMMARY",
        "=" * 80,
        "",
        response.strip(),
        "",
        "-" * 80,
        f"Execution Time: {execution_time:.2f} seconds",
        "=" * 80
    ]
    
    return "\n".join(formatted_output)