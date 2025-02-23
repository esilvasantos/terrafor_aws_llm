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
        
        # Ensure the formatted output is a string
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
    
    
    tables = {}
    for info in schema_info:
        table_name = info[0]
        if table_name not in tables:
            tables[table_name] = []
        tables[table_name].append({
            'column': info[1],
            'type': info[2],
            'default': info[3],
            'nullable': info[4]
        })

    
    schema_details = []
    for table, columns in tables.items():
        schema_details.append(f"Table: {table}")
        for col in columns:
            schema_details.append(
                f"  Column: {col['column']}\n"
                f"  Type: {col['type']}\n"
                f"  Default: {col['default']}\n"
                f"  Nullable: {col['nullable']}\n"
            )

    schema_str = "\n".join(schema_details)

    prompt = f"""
    Analyze this database schema and provide a detailed technical summary.
    Format the output exactly as follows, with clear sections:

    1. Schema Overview
       - Total number of tables
       - Schema complexity assessment
       - Overall architecture pattern (e.g., star schema, snowflake, etc.)

    2. Table Analysis
       - Key tables and their primary functions
       - Table relationships and dependencies
       - Potential bottlenecks or design concerns

    3. Data Structure Analysis
       - Primary key strategy
       - Foreign key relationships
       - Indexing patterns
       - Common data types used

    4. Security and Integrity
       - NULL constraints analysis
       - Default values patterns
       - Data validation rules
       - Potential security considerations

    5. Performance Considerations
       - Tables that might need optimization
       - Potential query performance issues
       - Suggestions for indexing
       - Data volume considerations

    6. Schema Best Practices
       - Adherence to naming conventions
       - Normalization assessment
       - Redundancy analysis
       - Improvement suggestions

    7. Business Logic Insights
       - Core business entities identified
       - Critical business processes supported
       - Data flow patterns
       - Integration points

    8. Maintenance and Scalability
       - Schema flexibility assessment
       - Future growth considerations
       - Potential maintenance challenges
       - Backup and recovery implications

    Schema details:
    {schema_str}
    
    Provide specific examples and detailed explanations for each section.
    Highlight both strengths and potential areas for improvement.
    """

    response = LLM.ask_ollama(prompt)
    execution_time = time.time() - start_time

    
    table_stats = f"""
    DETAILED STATISTICS
    ==================
    Total Tables: {len(tables)}
    Total Columns: {sum(len(cols) for cols in tables.values())}
    Average Columns per Table: {sum(len(cols) for cols in tables.values()) / len(tables):.2f}
    Tables with Primary Keys: {sum(1 for cols in tables.values() if any('primary key' in str(col).lower() for col in cols))}
    Nullable Columns: {sum(1 for cols in tables.values() for col in cols if col['nullable'] == 'YES')}
    """

    formatted_output = [
        "DATABASE SCHEMA ANALYSIS REPORT",
        "=" * 80,
        "",
        table_stats,
        "",
        "DETAILED ANALYSIS",
        "=" * 80,
        "",
        response.strip(),
        "",
        "-" * 80,
        f"Analysis completed in {execution_time:.2f} seconds",
        "",
        "RECOMMENDATIONS",
        "=" * 80,
        "1. Performance Optimization Suggestions",
        "2. Security Enhancement Recommendations",
        "3. Data Integrity Improvement Points",
        "4. Scaling Considerations",
        "",
        "Note: This analysis is based on schema structure only. Actual data patterns may affect these recommendations.",
        "=" * 80
    ]

    return "\n".join(formatted_output)