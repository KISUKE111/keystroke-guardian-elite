"""
Keystroke Guardian Elite
Real-time system monitoring & anomaly detection tool
Author: MOHAMED AMINE MOHAMMADI
"""
import psutil
import time
import os
import threading
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

folder_name = "7DI RASK HA ACHNO W9A3"
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
# KAT9AD L PATH DIAL L FOLDER (creating the folder path)
log_folder = os.path.join(desktop_path, folder_name)
# KATSAYB L FOLDER F7ALAT MAKANCH (create folder if it doesn't exist)
os.makedirs(log_folder, exist_ok=True)
# KAT9AD FILE INSIDE DAK L FOLDER LI GHADI N7TFO 3LIH L LOGS (create log file inside folder)
log_file = os.path.join(log_folder, "suspicious_log.txt")

trusted_processes = ["svchost.exe","explorer.exe","lsass.exe","wininit.exe","services.exe","system","idle"]
# KANHAYDO CASE SENSITIVITY (remove case sensitivity)
trusted_processes = [p.lower() for p in trusted_processes]  

trusted_processes = [p.lower() for p in ["svchost.exe","explorer.exe","lsass.exe","wininit.exe","services.exe","system","idle"]]

# HADI BACH N7SSBO CPU MZYAN (initialize CPU calculation correctly)
for p in psutil.process_iter():
    try:
        p.cpu_percent(interval=None)
    except:
        pass

process_history = {}
# tracking history dyal process (store process behavior over time)

logged_pids = set()
# HADI BACH MANKTBOSH NFS PROCESS KTR MN MERA (avoid logging same process multiple times)

running = False
search_text = ""
selected_pid = None
# HADI KATJIB GPU USAGE PER PROCESS MN NVIDIA-SMI (get GPU usage per process)
def get_gpu_usage_per_process():
    gpu_data = {}
    try:
        result = subprocess.check_output(
            ["nvidia-smi","--query-compute-apps=pid,used_memory","--format=csv,noheader,nounits"],
            encoding="utf-8",
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        for line in result.strip().split("\n"):
            if line:
                pid, mem = line.split(",")
                gpu_data[int(pid.strip())] = float(mem.strip())
    except:
        pass
    return gpu_data

def scan_system():
    global running

    while running:
        gpu_data = get_gpu_usage_per_process()

        for process in psutil.process_iter(['pid','name','memory_percent','status']):
            try:
                pid = process.info['pid']
                name = process.info['name']
                if not name:
                    continue

                name = name.lower()
                memory = process.info['memory_percent']
                status = process.info['status']
                cpu = process.cpu_percent(interval=None)
                gpu = gpu_data.get(pid, 0)

                # tracking history dyal process (store CPU/GPU over time)
                if pid not in process_history:
                    process_history[pid] = {"cpu": [], "gpu": []}

                process_history[pid]["cpu"].append(cpu)
                process_history[pid]["gpu"].append(gpu)

                # n7afdo ghir last values (keep last values only)
                process_history[pid]["cpu"] = process_history[pid]["cpu"][-15:]
                process_history[pid]["gpu"] = process_history[pid]["gpu"][-15:]

                avg_cpu = sum(process_history[pid]["cpu"]) / len(process_history[pid]["cpu"])
                avg_gpu = sum(process_history[pid]["gpu"]) / len(process_history[pid]["gpu"])

                risk = 0

                if name not in trusted_processes:
                    risk += 2

                if cpu > 60:
                    risk += 2

                if memory > 30:
                    risk += 2

                if avg_cpu > 50:
                    risk += 2

                
                # HADI KATKCHFO GPU ABUSE (detect GPU abuse behavior)
                if avg_gpu > 300 and avg_cpu > 40:
                    risk += 3

                # HADI KATZID RISK ILA GPU TALI M3A PROCESS UNKNOWN (increase risk if unknown process using GPU)
                if gpu > 200 and name not in trusted_processes:
                    risk += 2

                # search filter
                if search_text and search_text not in name:
                    continue

                update_table(pid, name, cpu, avg_cpu, memory, gpu, risk, status)

                # logging
                if risk >= 6 and pid not in logged_pids:
                    with open(log_file, "a") as f:
                        f.write(f"{datetime.now()} | {name} | PID:{pid} | CPU:{cpu:.1f} | GPU:{gpu:.1f} | Risk:{risk}\n")
                    logged_pids.add(pid)

            except:
                pass

        time.sleep(2)

def update_table(pid,name,cpu,avg_cpu,memory,gpu,risk,status):
    values = (name,pid,f"{cpu:.1f}",f"{avg_cpu:.1f}",f"{memory:.1f}",f"{gpu:.1f}",risk,status)

    if str(pid) in tree.get_children():
        tree.item(str(pid), values=values)
    else:
        tree.insert("", "end", iid=str(pid), values=values)

    if risk >= 7:
        tree.item(str(pid), tags=("high",))
    elif risk >= 4:
        tree.item(str(pid), tags=("medium",))
    else:
        tree.item(str(pid), tags=("low",))

def start_scan():
    global running
    if not running:
        running = True
        threading.Thread(target=scan_system, daemon=True).start()

def stop_scan():
    global running
    running = False

def kill_process():
    selected = tree.selection()
    if selected:
        pid = int(selected[0])
        try:
            psutil.Process(pid).terminate()
        except:
            pass

def update_search(event):
    global search_text
    search_text = search_entry.get().lower()

def on_select(event):
    global selected_pid
    selected = tree.selection()
    if selected:
        selected_pid = int(selected[0])

def update_graph():
    if selected_pid and selected_pid in process_history:
        ax.clear()
        ax.plot(process_history[selected_pid]["cpu"], label="CPU")
        ax.plot(process_history[selected_pid]["gpu"], label="GPU")
        ax.legend()
        ax.set_title(f"PID {selected_pid}")
        canvas.draw()
    app.after(1000, update_graph)

app = tk.Tk()
app.title("Keystroke Guardian Elite")
app.geometry("1100x700")
app.configure(bg="#121212")

top = tk.Frame(app, bg="#121212")
top.pack(fill="x")

tk.Label(top,text="🛡️ Guardian Elite",fg="white",bg="#121212",
         font=("Segoe UI",16,"bold")).pack(side="left", padx=10)

search_entry = tk.Entry(top,bg="#1e1e1e",fg="white")
search_entry.pack(side="right", padx=10)
search_entry.bind("<KeyRelease>", update_search)

columns=("Name","PID","CPU","Avg CPU","Memory","GPU(MB)","Risk","Status")
tree = ttk.Treeview(app,columns=columns,show="headings")

for col in columns:
    tree.heading(col,text=col)
    tree.column(col,width=120)

tree.pack(fill="both",expand=True)
tree.bind("<<TreeviewSelect>>", on_select)

tree.tag_configure("high",background="#3a1f1f")
tree.tag_configure("medium",background="#3a3320")
tree.tag_configure("low",background="#1e2f1e")

fig, ax = plt.subplots(figsize=(5,2))
canvas = FigureCanvasTkAgg(fig, master=app)
canvas.get_tk_widget().pack(fill="x")

bottom = tk.Frame(app,bg="#121212")
bottom.pack(fill="x")

tk.Button(bottom,text="Start",command=start_scan,bg="#1f6feb",fg="white").pack(side="left", padx=10)
tk.Button(bottom,text="Stop",command=stop_scan,bg="#8b0000",fg="white").pack(side="left")
tk.Button(bottom,text="Kill Process",command=kill_process,bg="#444",fg="white").pack(side="left", padx=10)

update_graph()
app.mainloop()