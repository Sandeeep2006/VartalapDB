import streamlit as st
import os
import pandas as pd
from dotenv import load_dotenv
from groq import Groq
from utils.mysqlconnector import MySqlConnector

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

st.set_page_config(
    page_title="VartalapDB",
    page_icon="💬"
)

#App Title
st.markdown("<h1 style='text-align: center;'>VartalapDB 💬</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Chat with your database using natural language</p>", unsafe_allow_html=True)


def get_llm_response(prompt):
    """Send a prompt to Groq LLM and return response."""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def validate_query(query, schema_info):
    """Validate generated SQL query."""
    prompt = f"""
    You are a SQL validator. Check this query:
    Query: "{query}"
    Database Schema: {schema_info}
    Respond 'VALID' or describe the issue.
    """
    return get_llm_response(prompt)

def iterative_query_generation(user_input, schema_info, max_retries=3):
    """Generate and refine SQL query using reflection pattern."""
    query_prompt = f"""
    Write a MySQL query for the user's request:
    "{user_input}"
    Use only these tables/columns: {schema_info}.
    Respond only with the SQL query. Do not include any backticks or anu other characters or word. Give RAW SQL.
    """
    query = get_llm_response(query_prompt)

    for _ in range(max_retries):
        validation = validate_query(query, schema_info)
        if "VALID" in validation:
            return query
        query_prompt += f"\nError: {validation}\nRewrite:"
        query = get_llm_response(query_prompt)

    return "Failed to generate a valid query."

#CSS
st.markdown("""
<style>
/* Hide ALL vertical block backgrounds */
div[data-testid="stVerticalBlock"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}

/* Hide the specific container that creates the grey box */
.element-container:has(.connection-form) {
    background: transparent !important;
}

.connection-form {
    max-width: 400px;
    padding: 20px;
    background-color: #262730;
    border: 1px solid #444;
    border-radius: 10px;
    margin: 20px auto;
}

.connection-form h2 { 
    color: #fafafa; 
    text-align: center; 
}

.stForm {
    background: transparent !important;
}
</style>
""", unsafe_allow_html=True)

# State variables
if "db_connected" not in st.session_state:
    st.session_state.db_connected = False
if "db_info" not in st.session_state:
    st.session_state.db_info = {}
if "messages" not in st.session_state:
    st.session_state.messages = []

# Database connection setup
if not st.session_state.db_connected:
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown("## Database Connection Setup 🔌")
        with st.form("db_connection"):
            host = st.text_input("Host", "localhost")
            user = st.text_input("User", "root")
            password = st.text_input("Password", type="password")
            database = st.text_input("Database", "my_database")
            submitted = st.form_submit_button("Connect", use_container_width=True)

            if submitted:
                with st.spinner("Connecting..."):
                    connection = MySqlConnector(host, user, password, database)
                    conn = connection.get_connection()
                    if conn is not None:
                        st.session_state.db_connected = True
                        st.session_state.db_info = {
                            "host": host, "user": user,
                            "password": password, "database": database
                        }
                        st.rerun()

# Main chat interface
else:
    mysql = MySqlConnector(**st.session_state.db_info)
    schema_info = mysql.get_basic_info()

    # Display previous messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle new user input
    if prompt := st.chat_input("Ask your database question..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Generate and execute query
        final_query = iterative_query_generation(prompt, schema_info)
        response = mysql.execute_pd_query(final_query)

        # Display assistant response
        with st.chat_message("assistant"):
            st.write(response)
        st.session_state.messages.append({"role": "assistant", "content": str(response)})