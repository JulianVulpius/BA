import socket
import keyboard
import threading
import time
from tkinter import (Tk, Label, Button, Frame, Listbox, Scrollbar, 
                     StringVar, BooleanVar, END, HORIZONTAL)
from tkinter import ttk

# Unicorn Configuration
UDP_IP = "127.0.0.1"
UDP_PORT = 1000

EVENT_TRIGGERS = {
    'n': ('1', 'Song Start'), 'm': ('2', 'Song or Playlist End'),
    'v': ('9', 'Transition Start'), 'b': ('10', 'Transition End'),
    'q': ('3', 'Visual Event Start'), 'w': ('4', 'Visual Event End'),
    'a': ('5', 'Auditory Event Start'), 's': ('6', 'Auditory Event End'),
    'y': ('7', 'Body Movement Start'), 'x': ('8', 'Body Movement End'),
}

class ManualTriggerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Unicorn Manual Trigger Control")
        self.root.minsize(500, 500)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Networking
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.endPoint = (UDP_IP, UDP_PORT)

        self.setup_ui()
        self.setup_keyboard_hooks()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.log_event("Manual Trigger App initialized. Waiting for input.")

    def setup_ui(self):
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0", font=('Helvetica', 10))

        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky='nsew')
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # --- Top Section: Activation & Info ---
        top_frame = ttk.LabelFrame(main_frame, text="Control", padding="10")
        top_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        
        self.manual_triggers_var = BooleanVar(value=True)
        self.chk_enable = ttk.Checkbutton(top_frame, text="Enable Keyboard Hotkeys", variable=self.manual_triggers_var)
        self.chk_enable.pack(anchor='w', pady=(0, 10))

        # Display Key Mapping nicely
        map_frame = ttk.Frame(top_frame)
        map_frame.pack(fill='x')
        
        ttk.Label(map_frame, text="Key Mapping:", font=('Helvetica', 10, 'bold')).grid(row=0, column=0, sticky='w', pady=(0,5))
        
        row, col = 1, 0
        for key, (val, desc) in EVENT_TRIGGERS.items():
            lbl_text = f"Key '{key.upper()}' -> {desc} ({val})"
            ttk.Label(map_frame, text=lbl_text).grid(row=row, column=col, sticky='w', padx=10, pady=2)
            col = 1 - col
            if col == 0: row += 1

        # --- Bottom Section: Logs ---
        log_frame = ttk.LabelFrame(main_frame, text="Trigger Log", padding="10")
        log_frame.grid(row=1, column=0, sticky='nsew')
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)

        # Last Trigger Label
        self.last_trigger_var = StringVar(value="Last Trigger: -")
        ttk.Label(log_frame, textvariable=self.last_trigger_var, font=('Helvetica', 10, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 5))

        # Listbox with Scrollbars
        log_scroll_frame = ttk.Frame(log_frame)
        log_scroll_frame.grid(row=1, column=0, columnspan=2, sticky='nsew')
        log_scroll_frame.grid_columnconfigure(0, weight=1)
        log_scroll_frame.grid_rowconfigure(0, weight=1)

        self.log_box = Listbox(log_scroll_frame, font=('Consolas', 9), fg="#333333", height=15)
        self.log_box.grid(row=0, column=0, sticky='nsew')

        scrollbar_y = Scrollbar(log_scroll_frame, orient="vertical", command=self.log_box.yview)
        scrollbar_y.grid(row=0, column=1, sticky='ns')
        scrollbar_x = Scrollbar(log_scroll_frame, orient=HORIZONTAL, command=self.log_box.xview)
        scrollbar_x.grid(row=1, column=0, sticky='ew')
        self.log_box.config(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        ttk.Button(log_frame, text="Clear Log", command=self.clear_log).grid(row=2, column=1, sticky='e', pady=(5, 0))

    def setup_keyboard_hooks(self):
        # Daemon thread to listen for global key presses
        threading.Thread(target=lambda: keyboard.hook(self.handle_key_press), daemon=True).start()

    def handle_key_press(self, event):
        if not self.manual_triggers_var.get(): return
        
        # Only trigger on key down
        if event.event_type == keyboard.KEY_DOWN and event.name in EVENT_TRIGGERS:
            trigger, desc = EVENT_TRIGGERS[event.name]
            # Use root.after to safely update GUI/Send from the thread
            self.root.after(0, self.send_trigger, trigger, desc)

    def send_trigger(self, trigger_value, event_desc):
        try:
            message = str(trigger_value)
            sendBytes = message.encode('utf-8')
            self.sock.sendto(sendBytes, self.endPoint)
            
            status_text = f"Sent '{trigger_value}' -> {event_desc}"
            self.last_trigger_var.set(f"Last Trigger: {status_text}")
            self.log_event(status_text)
            
        except Exception as e:
            self.last_trigger_var.set(f"Error sending trigger: {e}")
            self.log_event(f"ERROR: {e}")

    def log_event(self, message):
        time_str = time.strftime("%H:%M:%S")
        log_entry = f"[{time_str}] {message}"
        self.log_box.insert(0, log_entry)
        if self.log_box.size() > 200: self.log_box.delete(200)

    def clear_log(self):
        self.log_box.delete(0, END)

    def on_closing(self):
        self.sock.close()
        self.root.destroy()

if __name__ == "__main__":
    root = Tk()
    app = ManualTriggerApp(root)
    root.mainloop()