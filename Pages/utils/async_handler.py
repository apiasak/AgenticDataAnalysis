import asyncio
import threading
import time
from typing import Callable, Any, Optional
import streamlit as st

class AsyncTaskManager:
    """Manages asynchronous task execution for Streamlit apps"""
    
    def __init__(self):
        self.tasks = {}
        self.results = {}
        
    def submit_task(self, task_id: str, func: Callable, *args, **kwargs) -> str:
        """Submit a task for background execution"""
        def run_task():
            try:
                result = func(*args, **kwargs)
                self.results[task_id] = {
                    'status': 'completed',
                    'result': result,
                    'error': None,
                    'timestamp': time.time()
                }
            except Exception as e:
                self.results[task_id] = {
                    'status': 'failed',
                    'result': None,
                    'error': str(e),
                    'timestamp': time.time()
                }
        
        # Initialize task status
        self.results[task_id] = {
            'status': 'running',
            'result': None,
            'error': None,
            'timestamp': time.time()
        }
        
        # Start background thread
        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()
        self.tasks[task_id] = thread
        
        return task_id
    
    def get_task_status(self, task_id: str) -> dict:
        """Get the status of a task"""
        return self.results.get(task_id, {'status': 'not_found'})
    
    def is_task_complete(self, task_id: str) -> bool:
        """Check if a task is complete"""
        status = self.get_task_status(task_id)
        return status['status'] in ['completed', 'failed']
    
    def get_task_result(self, task_id: str) -> Any:
        """Get the result of a completed task"""
        status = self.get_task_status(task_id)
        if status['status'] == 'completed':
            return status['result']
        elif status['status'] == 'failed':
            raise Exception(status['error'])
        else:
            return None
    
    def cleanup_old_tasks(self, max_age_seconds: int = 3600):
        """Clean up old completed tasks"""
        current_time = time.time()
        to_remove = []
        
        for task_id, result in self.results.items():
            if current_time - result['timestamp'] > max_age_seconds:
                to_remove.append(task_id)
        
        for task_id in to_remove:
            self.results.pop(task_id, None)
            self.tasks.pop(task_id, None)

# Global task manager instance
if 'async_task_manager' not in st.session_state:
    st.session_state.async_task_manager = AsyncTaskManager()

def submit_analysis_task(chatbot, user_query, input_data_list):
    """Submit an analysis task for background processing"""
    task_manager = st.session_state.async_task_manager
    task_id = f"analysis_{int(time.time() * 1000)}"
    
    def analysis_task():
        return chatbot.user_sent_message(user_query, input_data=input_data_list)
    
    return task_manager.submit_task(task_id, analysis_task)

def check_analysis_progress(task_id):
    """Check the progress of an analysis task"""
    task_manager = st.session_state.async_task_manager
    return task_manager.get_task_status(task_id)

def get_analysis_result(task_id):
    """Get the result of a completed analysis task"""
    task_manager = st.session_state.async_task_manager
    return task_manager.get_task_result(task_id)
