import os
import logging
import json
import time
import streamlit as st
from openai import AzureOpenAI
from dotenv import load_dotenv
import uuid
import asyncio
import tempfile
import aiohttp
import base64

from netbox_tools.netbox_sites import netbox_sites
from netbox_tools.netbox_device_details import netbox_device_details   
from netbox_tools.netbox_prefixes import netbox_prefixes
from netbox_tools.netbox_child_prefixes import netbox_child_prefixes
from netbox_tools.netbox_ipaddresses import netbox_ipaddresses
from netbox_tools.netbox_interfaces import netbox_interfaces
from netbox_tools.netbox_search_roles import netbox_search_roles, netbox_get_all_roles

# Set up Streamlit page
st.set_page_config(page_title="Netbox AI Assistant", page_icon=":speech_balloon:")

# Load environment variables from .env file
load_dotenv()

def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

# Assuming your script is in the root of your project
image_path = os.path.join("assets", "netbox_ai_avatar_64x64.png")
avatar_base64 = get_image_base64(image_path)
avatar_url = f"data:image/png;base64,{avatar_base64}"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-05-01-preview"
)

# Custom CSS to center the title
st.markdown("""
    <style>
    .centered-title {
        text-align: center;
        font-size: 3rem;
        font-weight: bold;
        padding-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# Display the centered title
st.markdown("<h1 class='centered-title'>Netbox AI Assistant</h1>", unsafe_allow_html=True)


# Declare the Assistant's ID
assistant_id = os.environ.get('AZURE_OPENAI_ASSISTANT_ID')

# Initialize session state variables
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "openai_model" not in st.session_state:
    st.session_state.openai_model = "gpt-4o-mini"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tool_results" not in st.session_state:
    st.session_state.tool_results = {}
if "last_poll_run_status" not in st.session_state:
    st.session_state.last_poll_run_status = "Not started"

# Function to poll run status
async def poll_run(client, thread_id, run_id, timeout=300):
    start_time = time.time()
    status_placeholder = st.empty()
    while time.time() - start_time < timeout:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        st.session_state.current_run_status = run.status
        st.session_state.last_poll_run_status = run.status
        status_placeholder.text(f"Current status: {run.status}")
        print(f"Poll Run Status: {run.status}")  # Debug statement
        
        # Update the sidebar status
        if 'last_poll_status' in st.session_state:
            st.session_state.last_poll_status.text(f"Last Poll Run: {run.status}")
        
        if run.status in ['completed', 'requires_action', 'failed']:
            return run
        await asyncio.sleep(1)
    raise TimeoutError("Run polling timed out")

# Asynchronous function to handle tool execution
async def execute_tool(tool_call):
    tool_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    logger.info(f"Processing tool: {tool_name} with args: {arguments}")
    try:
        if tool_name == "netbox_sites":
            result = await netbox_sites(arguments)
        elif tool_name == "netbox_device_details":
            result = await netbox_device_details(arguments)
        elif tool_name == "netbox_prefixes":
            result = await netbox_prefixes(arguments)
        elif tool_name == "netbox_child_prefixes":
            result = await netbox_child_prefixes(arguments)
        elif tool_name == "netbox_ipaddresses":
            result = await netbox_ipaddresses(arguments)
        elif tool_name == "netbox_interfaces":
            result = await netbox_interfaces(arguments)
        elif tool_name == "netbox_search_roles":
            result = await netbox_search_roles(arguments)
        elif tool_name == "netbox_get_all_roles":
            result = await netbox_get_all_roles()
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        output = json.dumps(result)  # Convert the JSON object to a string
        # Store tool result
        st.session_state.tool_results[tool_name] = True
        return {"tool_call_id": tool_call.id, "output": output}
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}")
        st.session_state.tool_results[tool_name] = False
        return {"tool_call_id": tool_call.id, "output": f"Error: {str(e)}"}


# Sidebar - Avatar at the top
st.sidebar.image("./assets/netbox_ai_avatar_sidebar-cropped.png", width=128)
st.sidebar.title("Settings and Status")

# Restart Session button
if st.sidebar.button("Restart Session"):
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.thread_id = None
    st.session_state.messages = []
    st.session_state.tool_results = {}
    st.session_state.last_poll_run_status = "Not started"
    st.rerun()

# Model selection dropdown
st.session_state.openai_model = "gpt-4o-mini"
st.sidebar.text(f"Model: {st.session_state.openai_model}")

# Display session information
st.sidebar.markdown("### Session Information")
st.sidebar.text(f"Session ID: {st.session_state.session_id}")

# Display tool results
st.sidebar.markdown("### Tool Results")
for tool, result in st.session_state.tool_results.items():
    st.sidebar.text(f"{tool}: {'Success' if result else 'Failed'}")

# Display poll run status
st.sidebar.markdown("### Poll Run Status")
st.session_state.last_poll_status = st.sidebar.empty()
st.session_state.last_poll_status.text(f"Last Poll Run: {st.session_state.last_poll_run_status}")

# File upload functionality
st.sidebar.markdown("### Upload Files")
uploaded_files = st.sidebar.file_uploader("Choose files", accept_multiple_files=True, type=['pdf', 'txt', 'doc', 'docx', 'html', 'json', 'ppt', 'md', 'py'])

if st.sidebar.button("Upload"):
    if uploaded_files:
        vector_store_id = os.getenv('AZURE_VECTORSTORE_ID')
        file_objects = []

        try:
            for uploaded_file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    # Use the original filename instead of the temporary filename
                    file_objects.append((uploaded_file.name, open(tmp_file.name, "rb")))

            # Use the upload_and_poll method to upload files and wait for processing
            file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store_id,
                files=file_objects
            )

            # Check the status of the upload
            if file_batch.status == "complete":
                st.sidebar.success(f"Files uploaded successfully! Status: {file_batch.status}")
                if hasattr(file_batch, 'file_counts'):
                    st.sidebar.info(f"File counts: {file_batch.file_counts}")
                else:
                    st.sidebar.info("Files processed, but count information is not available.")
            else:
                st.sidebar.warning(f"Upload status: {file_batch.status}")
                if hasattr(file_batch, 'file_counts'):
                    st.sidebar.info(f"File counts: {file_batch.file_counts}")
                else:
                    st.sidebar.info("File count information is not available.")

        except Exception as e:
            st.sidebar.error(f"An error occurred during file upload: {str(e)}")
            print(f"Detailed error: {str(e)}")  # This will print to your console for debugging

        finally:
            # Close and remove temporary files
            for _, file_obj in file_objects:
                file_obj.close()
                os.unlink(file_obj.name)

    else:
        st.sidebar.warning("Please upload at least one file.")

# Main chat area
if not st.session_state.thread_id:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    intro_message = "Hello! I'm your Netbox AI Assistant. You can ask me about IP addresses, devices, interfaces, locations and more. Start by asking my what I have in my toolbox."
    st.session_state.messages.append({"role": "assistant", "content": intro_message, "avatar": avatar_url})

# Display chat history
for message in st.session_state.messages:
    if message["role"] == "assistant":
        with st.chat_message("assistant", avatar=avatar_url):
            st.markdown(message["content"])
    else:
        with st.chat_message("user"):
            st.markdown(message["content"])

# Get user input
if prompt := st.chat_input("Enter your message"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Create message in the thread
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt
    )

    # Create and poll the run
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=assistant_id,
        model=st.session_state.openai_model
    )
    run = asyncio.run(poll_run(client, st.session_state.thread_id, run.id))

    # Handle different run statuses
    while run.status == 'requires_action':
        tool_calls = run.required_action.submit_tool_outputs.tool_calls
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tasks = [execute_tool(tool_call) for tool_call in tool_calls]
        tool_outputs = loop.run_until_complete(asyncio.gather(*tasks))

        # Submit tool outputs and poll again
        run = client.beta.threads.runs.submit_tool_outputs(
            thread_id=st.session_state.thread_id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )
        run = loop.run_until_complete(poll_run(client, st.session_state.thread_id, run.id))

    if run.status == 'completed':
        messages = client.beta.threads.messages.list(
            thread_id=st.session_state.thread_id
        )

        # Process and display assistant messages
        assistant_messages = [
            message for message in messages 
            if message.run_id == run.id and message.role == "assistant"
        ]
        for message in assistant_messages:
            content = message.content[0].text.value
            st.session_state.messages.append({"role": "assistant", "content": content, "avatar": avatar_url})
            with st.chat_message("assistant", avatar=avatar_url) as message:
                st.markdown(content)
    else:
        logger.error(f"Run ended with unexpected status: {run.status}")
        st.error(f"An error occurred: {run.status}")

    # Update the sidebar status one last time after completion
    if 'last_poll_status' in st.session_state:
        st.session_state.last_poll_status.text(f"Last Poll Run: {st.session_state.last_poll_run_status}")

    # Force a rerun to update the UI
    st.rerun()