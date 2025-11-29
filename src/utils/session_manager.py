import os
import shutil
import datetime
import streamlit as st

class SessionManager:
    def __init__(self, base_dir="workspace", db_path="state.db"):
        self.base_dir = os.path.abspath(base_dir)
        self.db_path = os.path.abspath(db_path)
        
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def get_all_sessions(self):
        """Returns a sorted list of session directories (newest first)."""
        if not os.path.exists(self.base_dir):
            return []
        sessions = [d for d in os.listdir(self.base_dir) if os.path.isdir(os.path.join(self.base_dir, d))]
        return sorted(sessions, reverse=True)

    def create_session(self, tag):
        """Creates a new session directory using the tag. Raises FileExistsError if it exists."""
        if not tag:
            raise ValueError("Tag is required.")
            
        # Sanitize tag
        safe_tag = "".join(c for c in tag if c.isalnum() or c in ('-', '_'))
        if not safe_tag:
             raise ValueError("Invalid tag format.")
             
        session_name = safe_tag
        path = os.path.join(self.base_dir, session_name)
        
        if os.path.exists(path):
            raise FileExistsError(f"Session '{session_name}' already exists.")
            
        os.makedirs(path)
        return session_name

    def clear_all_sessions(self):
        """Deletes all workspace folders and the database."""
        # Clear Workspace
        if os.path.exists(self.base_dir):
            for item in os.listdir(self.base_dir):
                item_path = os.path.join(self.base_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
        
        # Clear DB
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                st.error("Could not delete database file. It might be in use.")
                
    def get_workspace_path(self, session_id):
        return os.path.join(self.base_dir, session_id)
