from .manager import DatabaseManager

# Create a global instance of DatabaseManager
db_manager = DatabaseManager()

# Function to create server-specific tables
def create_server_tables(server_id):
    db_manager.create_server_tables(server_id)