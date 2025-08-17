# tools.py (Upgraded Production Version)

import pysnow
import pandas as pd
import chromadb
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
import config

# A mapping of ticket prefixes to their actual table names in ServiceNow
TICKET_TYPE_MAP = {
    "INC": "incident",
    "RITM": "sc_req_item",
    "CHG": "change_request",
    # You can add more types here, like "PRB" for problems, etc.
}


class ServiceNowTool:
    """A dedicated toolbox for all ServiceNow interactions."""
    def __init__(self):
        """Initializes the connection to ServiceNow."""
        try:
            self.client = pysnow.Client(
                instance=config.SNOW_INSTANCE,
                user=config.SNOW_USER,
                password=config.SNOW_PASSWORD,
            )
        except Exception as e:
            print(f"ERROR: Failed to connect to ServiceNow. Check config.py. Details: {e}")
            self.client = None
            
    def _get_table_name(self, ticket_number: str) -> str | None:
        """Identifies the table name from the ticket prefix."""
        for prefix, table in TICKET_TYPE_MAP.items():
            if ticket_number.upper().startswith(prefix):
                return table
        return None

    def get_ticket_details(self, ticket_number: str) -> str:
        """Fetches ticket details from the correct ServiceNow table."""
        if not self.client:
            return "Error: ServiceNow client not initialized."

        table_name = self._get_table_name(ticket_number)
        if not table_name:
            return f"Error: Unknown ticket type for '{ticket_number}'. Cannot determine table."

        # Dynamically create the API resource based on the identified table
        incident_api = self.client.resource(api_path=f"/table/{table_name}")
        response = incident_api.get(query={"number": ticket_number}).one_or_none()
        
        if not response:
            return f"Error: Ticket '{ticket_number}' not found in table '{table_name}'."

        # Get common fields, using .get() for safety
        short_desc = response.get('short_description', 'N/A')
        desc = response.get('description', 'N/A')
        comments = response.get('comments', 'N/A')

        details = (
            f"Ticket Number: {response.get('number', 'N/A')}\n"
            f"Short Description: {short_desc}\n"
            f"Description: {desc}\n"
            f"Latest Comments: {comments}"
        )
        return details

    def reassign_ticket(self, ticket_number: str, new_group_id: str, comment: str) -> str:
        """Reassigns a ticket in the correct table and adds a comment."""
        if not self.client:
            return "Error: ServiceNow client not initialized."

        table_name = self._get_table_name(ticket_number)
        if not table_name:
            return f"Error: Cannot reassign unknown ticket type '{ticket_number}'."

        incident_api = self.client.resource(api_path=f"/table/{table_name}")
        response = incident_api.get(query={"number": ticket_number})
        incident_sys_id = response.one()['sys_id']
        
        update_payload = {"assignment_group": new_group_id, "comments": comment}
        incident_api.update(query={'sys_id': incident_sys_id}, payload=update_payload)
        return f"Ticket {ticket_number} successfully reassigned."

class KnowledgeBaseRetriever:
    """A dedicated toolbox for searching the team knowledge base."""
    # This class does not need any changes.
    def __init__(self, csv_path: str = "data/teams_knowledge_base.csv"):
        self.vectorstore = self._load_and_embed(csv_path)

    def _load_and_embed(self, csv_path: str):
        try:
            df = pd.read_csv(csv_path)
            df['combined_text'] = "Team: " + df['group_name'] + ". Responsibilities: " + df['scope_description']
            embedding_function = OllamaEmbeddings(model="nomic-embed-text")
            return Chroma.from_texts(texts=df['combined_text'].tolist(), embedding=embedding_function, metadatas=df.to_dict('records'))
        except Exception as e:
            print(f"ERROR: Failed to load knowledge base from {csv_path}. Details: {e}")
            return None

    def find_relevant_teams(self, query: str, top_k: int = 5) -> list:
        if not self.vectorstore: return []
        results = self.vectorstore.similarity_search(query, k=top_k)
        return [{"group_name": doc.metadata.get("group_name", ""),"group_id": doc.metadata.get("group_id", ""),"scope": doc.metadata.get("scope_description", "")} for doc in results]