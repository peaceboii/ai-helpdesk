import threading
import time
import json
import traceback
from typing import Dict, Any, Optional
from app.connectors.factory import ConnectorFactory
from app.services.ticket_service import TicketService
from app.services.database_service import IntegrationRepository

class ListenerServiceManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ListenerServiceManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.ticket_service = TicketService()
        self.running_listeners = {} # integration_id -> { "thread": Thread, "stop_event": Event, "settings_hash": str }
        self.manager_thread = None
        self.stop_manager_event = threading.Event()

    def start(self):
        """Starts the main background manager daemon."""
        if self.manager_thread and self.manager_thread.is_alive():
            return
        self.stop_manager_event.clear()
        self.manager_thread = threading.Thread(target=self._run_manager, name="ListenerManager", daemon=True)
        self.manager_thread.start()
        print("Listener Service Manager daemon started successfully.")

    def stop(self):
        """Stops all background listeners and the manager."""
        self.stop_manager_event.set()
        for integration_id in list(self.running_listeners.keys()):
            self._stop_listener(integration_id)
        if self.manager_thread:
            self.manager_thread.join(timeout=5)
        print("Listener Service Manager stopped.")

    def _run_manager(self):
        while not self.stop_manager_event.is_set():
            try:
                # Poll SQLite settings for all integrations
                for integration_id in ["email", "telegram", "slack", "whatsapp", "website"]:
                    settings_data = IntegrationRepository.get_settings(integration_id)
                    enabled = settings_data.get("enabled", False)
                    settings = settings_data.get("settings", {})
                    
                    # Compute settings hash to detect changes
                    settings_str = json.dumps(settings, sort_keys=True)
                    settings_hash = hash(settings_str)
                    
                    is_running = integration_id in self.running_listeners and self.running_listeners[integration_id]["thread"].is_alive()
                    
                    if enabled:
                        if not is_running:
                            print(f"Starting background listener for {integration_id}...")
                            self._start_listener(integration_id, settings, settings_hash)
                        else:
                            # If running, check if settings changed
                            old_hash = self.running_listeners[integration_id]["settings_hash"]
                            if settings_hash != old_hash:
                                print(f"Settings changed for {integration_id}. Restarting background listener...")
                                self._stop_listener(integration_id)
                                self._start_listener(integration_id, settings, settings_hash)
                    else:
                        if is_running:
                            print(f"Stopping background listener for {integration_id} (disabled)...")
                            self._stop_listener(integration_id)
            except Exception as e:
                print(f"Error in Listener Manager loop: {e}")
                traceback.print_exc()
            # Check every 5 seconds
            time.sleep(5)

    def _start_listener(self, integration_id: str, settings: Dict[str, Any], settings_hash: str):
        stop_event = threading.Event()
        
        if integration_id == "email":
            target_fn = self._email_listener_loop
        elif integration_id == "telegram":
            target_fn = self._telegram_listener_loop
        else:
            target_fn = self._webhook_heartbeat_loop
            
        thread = threading.Thread(
            target=target_fn,
            args=(integration_id, settings, stop_event),
            name=f"{integration_id}_listener",
            daemon=True
        )
        thread.start()
        self.running_listeners[integration_id] = {
            "thread": thread,
            "stop_event": stop_event,
            "settings_hash": settings_hash
        }

    def _stop_listener(self, integration_id: str):
        if integration_id in self.running_listeners:
            self.running_listeners[integration_id]["stop_event"].set()
            self.running_listeners[integration_id]["thread"].join(timeout=2)
            del self.running_listeners[integration_id]
            IntegrationRepository.update_logs(integration_id, connection_status="Disconnected", add_log_message="Listener service stopped.")

    def _email_listener_loop(self, integration_id: str, settings: Dict[str, Any], stop_event: threading.Event):
        IntegrationRepository.update_logs(integration_id, connection_status="Connected", add_log_message="Email polling listener started.")
        
        try:
            interval = int(settings.get("polling_interval", 30))
        except ValueError:
            interval = 30
            
        while not stop_event.is_set():
            try:
                connector = ConnectorFactory.get_connector(integration_id, settings)
                status = connector.test_connection()
                IntegrationRepository.update_logs(integration_id, connection_status=status)
                
                if status == "Connected":
                    connector.process_and_move_emails(self.ticket_service.process_incoming_ticket)
                elif status == "Authentication Failed":
                    IntegrationRepository.update_logs(integration_id, increment_errors=True, add_log_message="Authentication failed. Please verify email credentials.")
                    time.sleep(min(interval * 2, 60))
                    continue
                else:
                    IntegrationRepository.update_logs(integration_id, increment_errors=True, add_log_message="Could not connect to IMAP server.")
            except Exception as e:
                err_msg = f"Email listener error: {e}"
                IntegrationRepository.update_logs(integration_id, increment_errors=True, add_log_message=err_msg)
                
            # Sleep in 1-second ticks
            for _ in range(interval):
                if stop_event.is_set():
                    break
                time.sleep(1)

    def _telegram_listener_loop(self, integration_id: str, settings: Dict[str, Any], stop_event: threading.Event):
        IntegrationRepository.update_logs(integration_id, connection_status="Connected", add_log_message="Telegram update polling listener started.")
        offset = 0
        
        while not stop_event.is_set():
            try:
                connector = ConnectorFactory.get_connector(integration_id, settings)
                status = connector.test_connection()
                IntegrationRepository.update_logs(integration_id, connection_status=status)
                
                if status == "Connected":
                    offset = connector.process_polling_updates(offset, self.ticket_service.process_incoming_ticket)
                elif status == "Invalid Token":
                    IntegrationRepository.update_logs(integration_id, increment_errors=True, add_log_message="Invalid Telegram bot token.")
                    time.sleep(30)
                    continue
                else:
                    IntegrationRepository.update_logs(integration_id, increment_errors=True, add_log_message="Could not connect to Telegram API.")
            except Exception as e:
                err_msg = f"Telegram listener error: {e}"
                IntegrationRepository.update_logs(integration_id, increment_errors=True, add_log_message=err_msg)
                time.sleep(10)
                
            time.sleep(2)

    def _webhook_heartbeat_loop(self, integration_id: str, settings: Dict[str, Any], stop_event: threading.Event):
        """Monitor connection status for webhook-based integrations (Slack, WhatsApp, Website)."""
        IntegrationRepository.update_logs(integration_id, connection_status="Connected", add_log_message="Webhook listener monitor started.")
        
        while not stop_event.is_set():
            try:
                connector = ConnectorFactory.get_connector(integration_id, settings)
                status = connector.test_connection()
                IntegrationRepository.update_logs(integration_id, connection_status=status)
            except Exception as e:
                IntegrationRepository.update_logs(integration_id, connection_status="Disconnected", add_log_message=f"Status monitor error: {e}")
                
            for _ in range(60):
                if stop_event.is_set():
                    break
                time.sleep(1)
