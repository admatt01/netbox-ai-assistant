# NetBox AI Assistant

## Project Overview
The NetBox AI Assistant is a powerful tool built with Azure OpenAI Foundry (formerly Azure OpenAI Studio) that leverages the NetBox community edition GraphQL API to query NetBox data. It presents this data through a user-friendly Streamlit-powered chat interface, saving users time by eliminating the need to navigate through multiple layers of the NetBox UI.

## Features
- **Blended Queries**: Users can ask complex questions about devices, such as their interface IP addresses, locations, and cable terminations in a single query.
- **Streamlit Interface**: A modern chat interface that enhances user interaction with the NetBox data.
- **Azure OpenAI Integration**: Utilizes Azure OpenAI for intelligent responses and data processing.

## Setup Instructions

### Azure AI Foundry Setup
1. **Create Azure OpenAI Resource**
   - Navigate to the Azure Portal.
   - Create a new OpenAI resource.
   - Select the appropriate region and pricing tier.

2. **Set Up Assistant**
   - In Azure AI Studio, create a new Assistant.
   - Configure the Assistant with the provided tool schemas.
   - Enable function calling capabilities.

3. **Configure Vector Store**
   - Create a new Vector Store in Azure AI Studio.
   - Configure the vector embeddings model.
   - Set up the appropriate indexing strategy.

4. **Obtain API Keys**
   - In Azure Portal, navigate to your OpenAI resource.
   - Under "Keys and Endpoint", copy:
     - Endpoint URL
     - API Key
     - Assistant ID
     - Vector Store ID

### Environment Variables
1. Rename the `env.txt` file to `.env`.
2. Open the `.env` file and enter your Azure OpenAI environment variables:
   ```
   AZURE_OPENAI_ENDPOINT=https://your-openai-endpoint.azure.com/
   AZURE_OPENAI_API_KEY=your-api-key
   AZURE_OPENAI_ASSISTANT_ID=your-assistant-id
   NETBOX_URL=https://your-netbox-url/graphql/
   NETBOX_TOKEN=your-netbox-token
   AZURE_VECTORSTORE_ID=your-vectorstore-id
   ```

### Setting Up a Python Virtual Environment

#### For Windows:
1. Open Command Prompt.
2. Navigate to your project directory.
3. Run the command: `python -m venv venv`
4. Activate the virtual environment with: `venv\Scripts\activate`
5. Install dependencies using: `pip install -r requirements.txt`

#### For Linux:
1. Open Terminal.
2. Navigate to your project directory.
3. Run the command: `python3 -m venv venv`
4. Activate the virtual environment with: `source venv/bin/activate`
5. Install dependencies using: `pip install -r requirements.txt`

### Installation
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/Netbox-AI-Assistant.git
   cd Netbox-AI-Assistant
   ```
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
1. Run the application:
   ```
   streamlit run Netbox_AI_Assistant.py
   ```
2. Open your web browser and navigate to `http://localhost:8501` to access the chat interface.

3. Start interacting with the assistant by asking questions about your NetBox data.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.
