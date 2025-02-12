import psycopg2
import pandas as pd
import numpy as np
import time
from config import Config
import logging

class Database:
    @staticmethod
    def create_connection():
        return psycopg2.connect(**Config.DB_PARAMS)

    @staticmethod
    def query_database(query):
        conn = None
        start_time = time.time()
        try:
            conn = Database.create_connection()
            cursor = conn.cursor()
            cursor.execute(query)

            if query.strip().lower().startswith("select"):
                columns = [desc[0] for desc in cursor.description]
                results = cursor.fetchall()
                df = pd.DataFrame(results, columns=columns)
                formatted_output = Database.format_query_results(results, columns, time.time() - start_time)
                return df, formatted_output
            else:
                conn.commit()
                execution_time = time.time() - start_time
                return f"Operation completed successfully. Execution time: {execution_time:.4f} seconds"
        except Exception as e:
            return f"Database error: {str(e)}"
        finally:
            if conn:
                conn.close()

    @staticmethod
    def format_query_results(results, columns, execution_time):
        col_widths = []
        for i, col in enumerate(columns):
            width = len(str(col))
            for row in results:
                width = max(width, len(str(row[i])))
            col_widths.append(width + 2)

        separator = "+" + "+".join("-" * width for width in col_widths) + "+"
        
        formatted_output = [
            "\nQuery Results",
            "=" * (len(separator)),
            separator,
            "| " + " | ".join(f"{col:<{width-2}}" for col, width in zip(columns, col_widths)) + " |",
            separator
        ]
        
        for row in results:
            formatted_row = "| " + " | ".join(f"{str(val):<{width-2}}" for val, width in zip(row, col_widths)) + " |"
            formatted_output.append(formatted_row)
        
        formatted_output.extend([
            separator,
            f"\nRows returned: {len(results)}",
            f"Execution time: {execution_time:.4f} seconds",
            "=" * (len(separator))
        ])
        
        return "\n".join(formatted_output)

    @staticmethod
    def get_schema_info(schema_name):
        query = """
        SELECT 
            t.table_name,
            c.column_name,
            c.data_type,
            c.column_default,
            c.is_nullable
        FROM information_schema.tables t
        JOIN information_schema.columns c 
            ON t.table_name = c.table_name 
            AND t.table_schema = c.table_schema
        WHERE t.table_schema = %s
        ORDER BY t.table_name, c.ordinal_position;
        """
        
        conn = Database.create_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (schema_name,))
            return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def get_table_statistics(schema_name, table_name):
        start_time = time.time() 
        try:
            conn = Database.create_connection()
            cursor = conn.cursor()
            
            column_query = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s;
            """
            cursor.execute(column_query, (schema_name, table_name))
            columns = cursor.fetchall()
            
            formatted_output = f"TABLE STATISTICS: {schema_name}.{table_name}\n"
            formatted_output += "=" * 80 + "\n\n"
            
            stats = {}
            for col, dtype in columns:
                formatted_output += f"Column: {col}\n"
                formatted_output += "-" * 40 + "\n"
                formatted_output += f"Data Type: {dtype}\n"
                
                if dtype in ('integer', 'numeric', 'double precision'):
                    stats_query = f"""
                    SELECT 
                        COUNT(*) as count,
                        AVG({col}) as mean,
                        MIN({col}) as min,
                        MAX({col}) as max,
                        COUNT(DISTINCT {col}) as unique_count
                    FROM {schema_name}.{table_name}
                    WHERE {col} IS NOT NULL;
                    """
                    cursor.execute(stats_query)
                    result = cursor.fetchone()
                    
                    stats[col] = {
                        'type': 'numeric',
                        'count': result[0],
                        'mean': result[1],
                        'min': result[2],
                        'max': result[3],
                        'unique_values': result[4]
                    }
                    
                    formatted_output += f"Count: {result[0]}\n"
                    formatted_output += f"Mean: {result[1]:.2f}\n"
                    formatted_output += f"Min: {result[2]}\n"
                    formatted_output += f"Max: {result[3]}\n"
                    formatted_output += f"Unique Values: {result[4]}\n"
                else:
                    stats_query = f"""
                    SELECT 
                        COUNT(*) as count,
                        COUNT(DISTINCT {col}) as unique_count
                    FROM {schema_name}.{table_name}
                    WHERE {col} IS NOT NULL;
                    """
                    cursor.execute(stats_query)
                    result = cursor.fetchone()
                    
                    stats[col] = {
                        'type': 'categorical',
                        'count': result[0],
                        'unique_values': result[1]
                    }
                    
                    formatted_output += f"Count: {result[0]}\n"
                    formatted_output += f"Unique Values: {result[1]}\n"
                
                formatted_output += "\n"
            
            execution_time = time.time() - start_time
            formatted_output += f"\nExecution Time: {execution_time:.4f} seconds\n"
            formatted_output += "=" * 80 + "\n"
            
            return stats, formatted_output
            
        finally:
            if conn:
                conn.close()