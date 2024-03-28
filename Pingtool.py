import tkinter as tk
from tkinter import ttk, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from pythonping import ping
import threading
import queue
import datetime

# Function to perform ping in a separate thread
def ping_thread(ip, stop_event):
    while not stop_event.is_set():
        response = ping(ip, count=1, timeout=1)
        response_time = response.rtt_avg_ms if response.success() else 1000
        data_queue.put((ip, response_time))
        stop_event.wait(1)

# Global queue for ping data
data_queue = queue.Queue()
threads = {}
stop_events = {}

def start_pinging(ip):
    if ip in threads and threads[ip].is_alive():
        return
    stop_events[ip] = threading.Event()
    thread = threading.Thread(target=ping_thread, args=(ip, stop_events[ip]))
    thread.start()
    threads[ip] = thread

def stop_pinging(ip):
    if ip in stop_events:
        stop_events[ip].set()
        del stop_events[ip]
        del threads[ip]

def stop_all():
    for ip in list(stop_events.keys()):
        stop_pinging(ip)

# GUI application
class PingApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ping Monitor")
        self.geometry("800x600")

        # PanedWindow for resizable split window effect
        self.paned_window = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief=tk.RAISED)
        self.paned_window.pack(fill=tk.BOTH, expand=1)

        # Top frame for the text input area for the IPs
        self.top_frame = tk.Frame(self.paned_window)
        self.ip_text = tk.Text(self.top_frame, height=10, width=50)  # Changed to use Text widget
        self.ip_text.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.BOTH)
        self.ip_text.bind('<Return>', self.insert_newline)  # Bind Return key to insert_newline function
        self.paned_window.add(self.top_frame)

        # Bottom frame for matplotlib plot
        self.bottom_frame = tk.Frame(self.paned_window)
        self.fig = Figure(figsize=(7, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.bottom_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.paned_window.add(self.bottom_frame)

        # Control Buttons on the right side
        self.buttons_frame = tk.Frame(self.top_frame)
        self.start_button = ttk.Button(self.buttons_frame, text="Start Pinging", command=self.start)
        self.start_button.pack(fill=tk.X, pady=2)
        self.stop_all_button = ttk.Button(self.buttons_frame, text="Stop All", command=stop_all)
        self.stop_all_button.pack(fill=tk.X, pady=2)
        self.save_button = ttk.Button(self.buttons_frame, text="Save Plot", command=self.save_plot)
        self.save_button.pack(fill=tk.X, pady=2)
        self.buttons_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Data storage and update plot
        self.response_times = {}
        self.update_plot()
        
    def insert_newline(self, event):
        """Inserts a newline at the current cursor position."""
        self.ip_text.insert(tk.INSERT, '\n')
        return 'break'  # Prevents the default behavior of the Return key
    
    def start(self):
        text_content = self.ip_text.get("1.0", "end-1c")
        ips = text_content.replace('\n', ',').split(',')
        for ip in ips:
            ip = ip.strip()
            if ip:  # Ensure it's not an empty string
                start_pinging(ip)
                if ip not in self.response_times:
                    self.response_times[ip] = []

    def update_plot(self):
        try:
            while not data_queue.empty():
                ip, response_time = data_queue.get()
                if ip in self.response_times:
                    self.response_times[ip].append(response_time)
                else:
                    self.response_times[ip] = [response_time]
        except queue.Empty:
            pass

        self.ax.clear()
        for ip, times in self.response_times.items():
            self.ax.plot(times, label=ip)
        self.ax.legend(loc='upper left')
        self.canvas.draw()

        self.after(1000, self.update_plot)

    def save_plot(self):
        # Generate a unique filename with the current datetime
        filename = f"ping_plot_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
        # Ask user where to save the file, defaulting to the generated filename
        filepath = filedialog.asksaveasfilename(defaultextension=".png", initialfile=filename)
        if filepath:
            self.fig.savefig(filepath)

if __name__ == "__main__":
    app = PingApplication()
    app.mainloop()

    stop_all()
