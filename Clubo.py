import os
import streamlit as st
from io import StringIO
import re
import sys
from modules.history import ChatHistory
from modules.layout import Layout
from modules.utils import Utilities

# To be able to update the changes made to modules in localhost (press r)
def reload_module(module_name):
    import importlib
    import sys
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
    return sys.modules[module_name]

history_module = reload_module('modules.history')
layout_module = reload_module('modules.layout')
utils_module = reload_module('modules.utils')

ChatHistory = history_module.ChatHistory
Layout = layout_module.Layout
Utilities = utils_module.Utilities

st.set_page_config(layout="wide", page_icon="💬", page_title="Clubo Chat-Bot 🤖")

# Custom CSS to hide the deploy button and the menu
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Initialize session state variables
if 'model' not in st.session_state:
    st.session_state['model'] = 'gpt-3.5-turbo'
if 'temperature' not in st.session_state:
    st.session_state['temperature'] = 0.0
if 'reset_chat' not in st.session_state:
    st.session_state['reset_chat'] = False
if 'ready' not in st.session_state:
    st.session_state['ready'] = True

# Instantiate the main components
layout, utils = Layout(), Utilities()

layout.show_header("PDF, TXT, CSV")

user_api_key = user_api_key = utils.load_api_key()

if not user_api_key:
    st.error("No API key found. Please add an API key to your secrets.")
else:
    os.environ["OPENAI_API_KEY"] = user_api_key

    uploaded_file = utils.handle_upload(["pdf"])

    if uploaded_file:

        # Initialize chat history
        history = ChatHistory()
        try:
            chatbot = utils.setup_chatbot(
                uploaded_file, st.session_state["model"], st.session_state["temperature"]
            )
            st.session_state["chatbot"] = chatbot

            if st.session_state["ready"]:
                # Create containers for chat responses and user prompts
                response_container, prompt_container = st.container(), st.container()

                with prompt_container:
                    # Display the prompt form
                    is_ready, user_input = layout.prompt_form()

                    # Initialize the chat history
                    history.initialize(uploaded_file)

                    # Reset the chat history if button clicked
                    if st.session_state["reset_chat"]:
                        history.reset(uploaded_file)

                    if is_ready:
                        # Update the chat history and display the chat messages
                        history.append("user", user_input)

                        old_stdout = sys.stdout
                        sys.stdout = captured_output = StringIO()

                        output = st.session_state["chatbot"].conversational_chat(user_input)

                        sys.stdout = old_stdout

                        history.append("assistant", output)

                        # Clean up the agent's thoughts to remove unwanted characters
                        thoughts = captured_output.getvalue()
                        cleaned_thoughts = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', thoughts)
                        cleaned_thoughts = re.sub(r'\[1m>', '', cleaned_thoughts)

                history.generate_messages(response_container)
        except Exception as e:
            st.error(f"Error: {str(e)}")
