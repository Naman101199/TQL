import streamlit as st
import sys
import os
sys.path.append('../utils/')
from utils import *
import requests
import json
import pandas as pd

import time

from sql_formatter.core import format_sql

def style():
    st.markdown(
        """
        <style>
        .st-eb {
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0px 0px 8px rgba(0, 0, 0, 0.2);
        }
        .st-cu {
            background-color: #f0f0f0;
            padding: 0.5rem;
            border-radius: 0.25rem;
        }
        .st-dp {
            padding: 1rem;
        }
        .st-eb, .st-cu {
            margin: 1rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def parse_excel_file(uploaded_file):
    
    df_table = pd.read_excel(uploaded_file, sheet_name = 'Tables')
    df_fks = pd.read_excel(uploaded_file, sheet_name = 'ForeignKeys')
    
    df_list = []
    for i in range(len(df_table)):
        temp = []
        rows = df_table.iloc[i]['DDL'].replace('CREATE TABLE', '').replace('(', '+').replace(')', '').split('+')
        table_name = rows[0].strip()
        temp.append('user_input')
        temp.append(table_name)
        temp.append(table_name)
        if('PRIMARY KEY' in rows[1]):
            temp.append(rows[-1])
            rows[1] = rows[1].replace('PRIMARY KEY', '')
        else:
            temp.append('NO PRIMARY KEY')
        columns = []
        data_types = []
        for j in rows[1].strip().split(', '):
            columns.append(j.split()[0])

            if(j.split()[1] == 'VARCHAR'):
                data_types.append('text')
            else:
                data_types.append('number')
        temp.append(columns)
        temp.append(columns)
        temp.append(data_types)
        temp.append([])

        df_list.append(temp)

    return \
        pd.DataFrame(df_list).rename(columns = {
            0: 'schema_id',
            1: 'table_name',
            2: 'table_name_original',
            3: 'primary_key',
            4: 'column_list',
            5: 'column_list_original',
            6: 'column_datatypes', 
            7: 'foreign_keys'
        })

def main():
    st.set_page_config(
        page_title="TQL – Text to SQL",
        page_icon="🛢️",
        layout="wide",
    )
    style()

    st.title("TQL – Text to SQL")
    
    if "old_queries" not in st.session_state:
        st.session_state['old_queries'] = []
    # Layout the sidebar for older queries
    with st.sidebar:
        st.markdown("# Older Queries")
        for i in st.session_state['old_queries'][::-1]:
            st.markdown(i[0])
            st.code(i[1])
            st.text('----')

    st.subheader("New Query")

    # Select a test schema from a dropdown
    schema = st.selectbox("Select a test schema from dropdown", ["Excel Upload", "college_2", "yelp", "student_assessment"])

    s = pd.DataFrame()
    if(schema == "Excel Upload"):
        uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

        if uploaded_file is not None:
            st.write("File uploaded successfully!")

            try:
                s = parse_excel_file(uploaded_file)
                show_df = s[['table_name', 'primary_key', 'column_list']].reset_index(drop = True)\
                .rename(columns = {
                    'table_name' : 'Name of Table', 
                    'primary_key' : 'Primary Key', 
                    'column_list': 'List of Columns', 
                    'foreign_keys' : 'Foreign Keys'
                })
                st.dataframe(show_df, use_container_width = True, hide_index = True)
            except Exception as e:
                st.error(f"Error while uploading the file: {e}")

    else:
        q, s = get_spider_schema_table_files()
        s = s[s['schema_id'] == schema]
        show_df = s[['table_name', 'primary_key', 'column_list']].reset_index(drop = True)\
        .rename(columns = {
            'table_name' : 'Name of Table', 
            'primary_key' : 'Primary Key', 
            'column_list': 'List of Columns', 
            'foreign_keys' : 'Foreign Keys'
        })
        st.dataframe(show_df, use_container_width = True, hide_index = True)

    # Enter query
    query = st.text_area("Enter query:", height=200)

    if st.button("Run Query"):
        if query.strip() == "":
            st.error("Please enter a query.")
        else:
            # Call your function to convert TQL to SQL
            processed_text = ''
            url_api = 'https://1bd8-34-133-103-51.ngrok-free.app/api/data'
            
            with st.spinner(text = '''      Parsing tables...'''):
                time.sleep(2)
            with st.spinner('   Generating the SQL Query...'):
                response = requests.post(url_api, json = {"schema" : schema, "query" : query, "dataframe" : s.to_json()})
                print(response.content)
            
            st.success("Generated SQL Query:")
            formatted_sql = format_sql(json.loads(response.content)['final_SQL_query'])
            st.code(formatted_sql ,language="sql")
            st.session_state['old_queries'].append([
                ':gray[**Question:**] ' + query,
                formatted_sql
            ])
                    

if __name__ == '__main__':
    main()
