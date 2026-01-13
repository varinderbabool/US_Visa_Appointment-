#!/usr/bin/env python3
"""GUI version of US Visa Appointment Automation Bot."""
import tkinter as tk
from tkinter import messagebox, scrolledtext
from tkcalendar import DateEntry
import threading
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Import settings for consulates
from settings import CONSULATES

# Default values
DEFAULT_TELEGRAM_TOKEN = '8035456582:AAGFF8HJBjepiL7eg_oIEVwdMQmWWCiJIkA'
DEFAULT_CHAT_ID = '2023815877'
DEFAULT_CHECK_INTERVAL = 30
DEFAULT_EARLIEST_DATE = '2026-01-31'
DEFAULT_LATEST_DATE = '2026-12-31'
DEFAULT_CURRENT_DATE = '2027-06-30'
DEFAULT_LOCATION = 'Toronto'

class VisaBotGUI:
    def __init__(self, root: tk.Tk) -> None:
        """Initialize the GUI application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("US Visa Appointment Bot - GUI")
        self.root.configure(bg="#1e1e1e")
        self.root.geometry("900x700")
        
        # Process tracking
        self.bot_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.stop_event = threading.Event()  # For proper thread stopping
        
        self.build_inputs()
        self.build_controls()
        self.build_log_area()
        
    def build_inputs(self) -> None:
        """Build input fields for the GUI."""
        input_frame = tk.Frame(self.root, bg="#1e1e1e")
        input_frame.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="ew")
        
        def label(text, row, col=0):
            lbl = tk.Label(input_frame, text=text, bg="#1e1e1e", fg="#ffffff", font=("Arial", 10))
            lbl.grid(row=row, column=col, sticky="w", pady=5)
            return lbl
        
        # Email
        label("Email:", 0).grid(row=0, column=0, sticky="w", pady=5)
        self.email_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=self.email_var, width=40, font=("Arial", 10)).grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Password
        label("Password:", 1).grid(row=1, column=0, sticky="w", pady=5)
        self.password_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=self.password_var, show="*", width=40, font=("Arial", 10)).grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        # Location
        label("Location:", 2).grid(row=2, column=0, sticky="w", pady=5)
        self.location_var = tk.StringVar(value=DEFAULT_LOCATION)
        location_menu = tk.OptionMenu(input_frame, self.location_var, *CONSULATES.keys())
        location_menu.config(width=37, font=("Arial", 10))
        location_menu.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        # Earliest Date
        label("Earliest Date:", 3).grid(row=3, column=0, sticky="w", pady=5)
        self.earliest_date = DateEntry(
            input_frame, 
            width=12, 
            background="darkblue", 
            foreground="white", 
            date_pattern="yyyy-mm-dd",
            font=("Arial", 10)
        )
        self.earliest_date.set_date(datetime.strptime(DEFAULT_EARLIEST_DATE, "%Y-%m-%d"))
        self.earliest_date.grid(row=3, column=1, sticky="w", padx=10, pady=5)
        
        # Latest Date
        label("Latest Date:", 4).grid(row=4, column=0, sticky="w", pady=5)
        self.latest_date = DateEntry(
            input_frame, 
            width=12, 
            background="darkblue", 
            foreground="white", 
            date_pattern="yyyy-mm-dd",
            font=("Arial", 10)
        )
        self.latest_date.set_date(datetime.strptime(DEFAULT_LATEST_DATE, "%Y-%m-%d"))
        self.latest_date.grid(row=4, column=1, sticky="w", padx=10, pady=5)
        
        # Current Booking Date
        label("Current Booking Date:", 5).grid(row=5, column=0, sticky="w", pady=5)
        self.current_date = DateEntry(
            input_frame, 
            width=12, 
            background="darkblue", 
            foreground="white", 
            date_pattern="yyyy-mm-dd",
            font=("Arial", 10)
        )
        self.current_date.set_date(datetime.strptime(DEFAULT_CURRENT_DATE, "%Y-%m-%d"))
        self.current_date.grid(row=5, column=1, sticky="w", padx=10, pady=5)
        
        # Info label
        info_label = tk.Label(
            input_frame, 
            text="Default: Token, Chat ID (2023815877), Check Interval (30s) are pre-configured",
            bg="#1e1e1e", 
            fg="#888888", 
            font=("Arial", 8, "italic")
        )
        info_label.grid(row=6, column=0, columnspan=2, pady=5, sticky="w")
        
    def build_controls(self) -> None:
        """Build control buttons (Start, Stop, Quit)."""
        control_frame = tk.Frame(self.root, bg="#1e1e1e")
        control_frame.grid(row=1, column=0, columnspan=4, pady=10)
        
        self.start_button = tk.Button(
            control_frame, 
            text="Start Bot", 
            command=self.start_bot,
            width=18, 
            bg="#28a745", 
            fg="white",
            font=("Arial", 10, "bold")
        )
        self.start_button.grid(row=0, column=0, padx=10)
        
        self.stop_button = tk.Button(
            control_frame, 
            text="Stop Bot", 
            command=self.stop_bot,
            width=18, 
            bg="#ffc107", 
            fg="black",
            font=("Arial", 10, "bold"),
            state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=10)
        
        self.quit_button = tk.Button(
            control_frame, 
            text="Quit", 
            command=self.confirm_quit,
            width=18, 
            bg="#dc3545", 
            fg="white",
            font=("Arial", 10, "bold")
        )
        self.quit_button.grid(row=0, column=2, padx=10)
        
        self.status_label = tk.Label(
            control_frame, 
            text="Status: Idle", 
            bg="#1e1e1e", 
            fg="#00bcd4",
            font=("Arial", 10, "bold")
        )
        self.status_label.grid(row=0, column=3, padx=20)
        
    def build_log_area(self) -> None:
        """Build log display area for bot output."""
        log_frame = tk.Frame(self.root, bg="#1e1e1e")
        log_frame.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        
        tk.Label(
            log_frame, 
            text="Bot Logs:", 
            bg="#1e1e1e", 
            fg="#ffffff",
            font=("Arial", 10, "bold")
        ).pack(anchor="w")
        
        self.log_box = scrolledtext.ScrolledText(
            log_frame, 
            height=20, 
            width=100, 
            state='disabled',
            bg="#121212", 
            fg="lime", 
            font=("Consolas", 9),
            wrap=tk.WORD
        )
        self.log_box.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights for resizing
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
    def log(self, message: str) -> None:
        """Add message to log area.
        
        Args:
            message: Message text to display in the log area
        """
        self.log_box.configure(state='normal')
        self.log_box.insert(tk.END, message)
        self.log_box.see(tk.END)
        self.log_box.configure(state='disabled')
        self.root.update_idletasks()
        
    def start_bot(self) -> None:
        """Start the bot in a separate thread."""
        # Validate inputs
        email = self.email_var.get().strip()
        password = self.password_var.get().strip()
        
        if not email or not password:
            messagebox.showerror("Input Error", "Email and Password are required.")
            return
        
        # Validate email format
        if '@' not in email or '.' not in email.split('@')[1] if '@' in email else '':
            messagebox.showerror("Input Error", "Please enter a valid email address.")
            return
        
        # Validate password length
        if len(password) < 1:
            messagebox.showerror("Input Error", "Password cannot be empty.")
            return
        
        # Get and validate date values
        try:
            earliest = self.earliest_date.get_date().strftime("%Y-%m-%d")
            latest = self.latest_date.get_date().strftime("%Y-%m-%d")
            current = self.current_date.get_date().strftime("%Y-%m-%d")
            
            # Validate date logic
            earliest_date_obj = datetime.strptime(earliest, "%Y-%m-%d")
            latest_date_obj = datetime.strptime(latest, "%Y-%m-%d")
            current_date_obj = datetime.strptime(current, "%Y-%m-%d")
            
            if earliest_date_obj > latest_date_obj:
                messagebox.showerror("Date Error", "Earliest date must be before or equal to latest date.")
                return
            
            if current_date_obj < earliest_date_obj:
                messagebox.showerror("Date Error", "Current booking date should be within the date range.")
                return
                
        except ValueError as e:
            messagebox.showerror("Date Error", f"Invalid date format: {e}")
            return
        except Exception as e:
            messagebox.showerror("Date Error", f"Error processing dates: {e}")
            return
        
        # Update UI
        self.status_label.config(text="Status: Running", fg="#00ff00")
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.is_running = True
        self.stop_event.clear()  # Reset stop event
        
        self.log("="*60 + "\n")
        self.log("Starting US Visa Appointment Bot...\n")
        self.log(f"Email: {self.email_var.get()}\n")
        self.log(f"Location: {self.location_var.get()}\n")
        self.log(f"Earliest Date: {earliest}\n")
        self.log(f"Latest Date: {latest}\n")
        self.log(f"Current Booking: {current}\n")
        self.log("="*60 + "\n\n")
        
        # Start bot in separate thread
        self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
        self.bot_thread.start()
        
    def run_bot(self) -> None:
        """Run the bot with GUI inputs in a separate thread."""
        try:
            # Import main function
            from main import main as run_main
            
            # Get inputs from GUI
            email = self.email_var.get()
            password = self.password_var.get()
            location = self.location_var.get()
            
            # Validate date inputs
            try:
                earliest_date = self.earliest_date.get_date().strftime("%Y-%m-%d")
                latest_date = self.latest_date.get_date().strftime("%Y-%m-%d")
                current_booking_date = self.current_date.get_date().strftime("%Y-%m-%d")
            except Exception as e:
                self.log(f"[ERROR] Invalid date format: {e}\n")
                self.status_label.config(text="Status: Error", fg="#ff0000")
                self.start_button.config(state="normal")
                self.stop_button.config(state="disabled")
                self.is_running = False
                return
            
            telegram_token = DEFAULT_TELEGRAM_TOKEN
            telegram_chat_id = DEFAULT_CHAT_ID
            check_interval = DEFAULT_CHECK_INTERVAL
            
            # Prepare inputs dictionary for main()
            gui_inputs: Dict[str, Any] = {
                'email': email,
                'password': password,
                'telegram_token': telegram_token,
                'telegram_chat_id': telegram_chat_id,
                'location': location,
                'earliest_date': earliest_date,
                'latest_date': latest_date,
                'current_date': current_booking_date,
                'check_interval': check_interval
            }
            
            self.log(f"[INFO] Initializing bot with GUI inputs...\n")
            
            # Redirect stdout and stderr to log
            class LogWriter:
                def __init__(self, log_callback):
                    self.log_callback = log_callback
                    self.buffer = ""
                    
                def write(self, text: str) -> None:
                    if text.strip():
                        # Clean up log formatting for GUI display
                        text_clean = text.strip()
                        if text_clean:
                            self.log_callback(text_clean + "\n")
                            
                def flush(self) -> None:
                    pass
            
            # Redirect stdout and stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = LogWriter(self.log)
            sys.stderr = LogWriter(self.log)
            
            try:
                # Check if stop was requested before starting
                if self.stop_event.is_set():
                    return
                    
                # Run main with GUI inputs (this will skip the interactive prompts)
                run_main(gui_inputs=gui_inputs)
            except KeyboardInterrupt:
                self.log("[INFO] Bot interrupted by user\n")
            except Exception as e:
                self.log(f"[ERROR] Bot error: {e}\n")
                import traceback
                self.log(traceback.format_exc())
            finally:
                # Restore stdout/stderr
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                self.status_label.config(text="Status: Stopped", fg="#ffaa00")
                self.start_button.config(state="normal")
                self.stop_button.config(state="disabled")
                self.is_running = False
                self.stop_event.clear()  # Reset stop event for next run
                
        except Exception as e:
            self.log(f"[ERROR] Fatal error: {e}\n")
            import traceback
            self.log(traceback.format_exc())
            self.status_label.config(text="Status: Error", fg="#ff0000")
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.is_running = False
            self.stop_event.clear()
            
    def stop_bot(self) -> None:
        """Stop the bot by setting the stop event."""
        if self.is_running:
            self.is_running = False
            self.stop_event.set()  # Signal the thread to stop
            self.log("[INFO] Stopping bot...\n")
            self.status_label.config(text="Status: Stopping...", fg="#ffaa00")
        else:
            messagebox.showinfo("Info", "Bot is not running.")
            
    def confirm_quit(self) -> None:
        """Confirm before quitting the application."""
        if self.is_running:
            if messagebox.askyesno("Quit", "Bot is running. Stop and quit?"):
                self.stop_bot()
                self.root.after(1000, self.root.destroy)
        else:
            if messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
                self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = VisaBotGUI(root)
    root.mainloop()
