import tkinter as tk
from tkinter import ttk, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from pythonping import ping
import threading
import queue
import datetime  # Used for generating a unique filename

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

        self.ip_entry = tk.Entry(self, width=50)
        self.ip_entry.pack(pady=20)

        self.start_button = ttk.Button(self, text="Start Pinging", command=self.start)
        self.start_button.pack(pady=10)

        self.stop_all_button = ttk.Button(self, text="Stop All", command=stop_all)
        self.stop_all_button.pack(pady=10)

        self.save_button = ttk.Button(self, text="Save Plot", command=self.save_plot)
        self.save_button.pack(pady=10)

        self.fig = Figure(figsize=(7, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack()

        self.response_times = {}
        self.update_plot()

    def start(self):
        ips = self.ip_entry.get().replace('\n', ',').split(',')
        for ip in ips:
            ip = ip.strip()
            if ip:
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
