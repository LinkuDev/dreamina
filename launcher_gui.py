#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dreamina Multi-Instance Controller with GUI
Chạy và điều khiển nhiều instance của main.py từ một giao diện
"""

from encoding_fix import safe_print
import builtins
builtins.print = safe_print

import os
import sys
import subprocess
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import queue

class InstanceController:
    """Controller cho một instance của main.py"""
    def __init__(self, instance_id, config, workspace, python_cmd):
        self.instance_id = instance_id
        self.config = config
        self.workspace = workspace
        self.python_cmd = python_cmd
        self.process = None
        self.status = "stopped"  # stopped, running, completed, failed
        self.log_queue = queue.Queue()
        self.start_time = None
        self.end_time = None
        
    def get_env(self):
        """Lấy environment variables cho instance này"""
        cookies_base = self.config.get('COOKIES_BASE', 'cookies')
        outputs_base = self.config.get('OUTPUTS_BASE', 'outputs')
        
        # Parse aspect ratios
        aspect_ratios_str = self.config.get('ASPECT_RATIO', '16:9')
        aspect_ratios = [ratio.strip() for ratio in aspect_ratios_str.split(',')]
        
        # Get aspect ratio for this worker
        ratio_index = (self.instance_id - 1) % len(aspect_ratios)
        worker_aspect_ratio = aspect_ratios[ratio_index]
        
        env = os.environ.copy()
        env.update({
            'COOKIES_FOLDER': f"{cookies_base}{self.instance_id}",
            'PROMPT_FILE': f"prompts/{self.instance_id}.txt",
            'OUTPUT_DIR': f"{outputs_base}{self.instance_id}",
            'ASPECT_RATIO': worker_aspect_ratio,
            'IMAGE_COUNT': self.config.get('IMAGE_COUNT', '4'),
            'BROWSER_HEADLESS': self.config.get('BROWSER_HEADLESS', 'false')
        })
        
        if sys.platform.startswith('win'):
            env.update({
                'PYTHONIOENCODING': 'utf-8',
                'PYTHONLEGACYWINDOWSSTDIO': '1'
            })
        
        return env
    
    def stream_output(self, pipe, stream_type):
        """Stream output từ subprocess"""
        try:
            for line in iter(pipe.readline, ''):
                if line:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    self.log_queue.put((stream_type, timestamp, line.rstrip()))
            pipe.close()
        except Exception as e:
            self.log_queue.put(("error", "", f"Stream error: {e}"))
    
    def start(self):
        """Bắt đầu chạy instance"""
        if self.status == "running":
            return False
        
        self.status = "running"
        self.start_time = datetime.now()
        self.end_time = None
        
        env = self.get_env()
        
        try:
            encoding = 'utf-8' if sys.platform.startswith('win') else None
            
            self.process = subprocess.Popen(
                [self.python_cmd, 'main.py'],
                cwd=self.workspace,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding=encoding,
                errors='replace',
                bufsize=1
            )
            
            # Start output streaming threads
            threading.Thread(
                target=self.stream_output,
                args=(self.process.stdout, "stdout"),
                daemon=True
            ).start()
            
            threading.Thread(
                target=self.stream_output,
                args=(self.process.stderr, "stderr"),
                daemon=True
            ).start()
            
            # Start monitoring thread
            threading.Thread(
                target=self._monitor_process,
                daemon=True
            ).start()
            
            return True
            
        except Exception as e:
            self.status = "failed"
            self.log_queue.put(("error", "", f"Failed to start: {e}"))
            return False
    
    def _monitor_process(self):
        """Monitor process và cập nhật status"""
        if self.process:
            returncode = self.process.wait()
            self.end_time = datetime.now()
            
            if returncode == 0:
                self.status = "completed"
                self.log_queue.put(("info", "", "✅ Completed successfully"))
            else:
                self.status = "failed"
                self.log_queue.put(("error", "", f"❌ Failed with code: {returncode}"))
    
    def stop(self):
        """Dừng instance"""
        if self.process and self.status == "running":
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                self.status = "stopped"
                self.end_time = datetime.now()
                self.log_queue.put(("info", "", "⏹️ Stopped by user"))
                return True
            except:
                try:
                    self.process.kill()
                    self.process.wait()
                    self.status = "stopped"
                    self.end_time = datetime.now()
                    return True
                except:
                    return False
        return False
    
    def get_runtime(self):
        """Lấy thời gian chạy"""
        if self.start_time:
            end = self.end_time or datetime.now()
            delta = end - self.start_time
            return str(delta).split('.')[0]  # Format: HH:MM:SS
        return "00:00:00"


class LauncherGUI:
    """GUI để điều khiển nhiều instances"""
    def __init__(self, root):
        self.root = root
        self.root.title("Dreamina Multi-Instance Controller")
        self.root.geometry("1200x800")
        
        self.workspace = Path(__file__).parent
        self.env_file = self.workspace / ".env"
        self.python_cmd = self.detect_python_command()
        self.config = self.load_config()
        self.instances = []
        self.update_timer = None
        
        self.setup_ui()
        self.load_instances()
        self.start_update_loop()
    
    def detect_python_command(self):
        """Detect Python command"""
        import platform
        import shutil
        
        if platform.system() == "Windows":
            commands = ['python', 'py', 'python3']
        else:
            commands = ['python3', 'python', 'py']
        
        for cmd in commands:
            if shutil.which(cmd):
                try:
                    result = subprocess.run([cmd, '--version'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0 and 'Python' in result.stdout:
                        return cmd
                except:
                    continue
        
        return sys.executable
    
    def load_config(self):
        """Load config từ .env"""
        config = {}
        
        if not self.env_file.exists():
            messagebox.showerror("Error", "File .env không tồn tại!\nVui lòng tạo file .env trước.")
            return config
        
        with open(self.env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        
        return config
    
    def setup_ui(self):
        """Tạo giao diện"""
        # Top frame: Control buttons
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)
        
        ttk.Button(control_frame, text="▶️ Start All", 
                  command=self.start_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="⏹️ Stop All", 
                  command=self.stop_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🔄 Refresh", 
                  command=self.refresh_ui).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🗑️ Clear Logs", 
                  command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="Status: ").pack(side=tk.LEFT, padx=(20, 5))
        self.status_label = ttk.Label(control_frame, text="Ready", 
                                     foreground="green", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.LEFT)
        
        # Middle frame: Instance list
        list_frame = ttk.LabelFrame(self.root, text="Instances", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview for instances
        columns = ("ID", "Status", "Runtime", "Config", "Actions")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        
        self.tree.heading("ID", text="Instance")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Runtime", text="Runtime")
        self.tree.heading("Config", text="Configuration")
        self.tree.heading("Actions", text="")
        
        self.tree.column("ID", width=80, anchor=tk.CENTER)
        self.tree.column("Status", width=100, anchor=tk.CENTER)
        self.tree.column("Runtime", width=100, anchor=tk.CENTER)
        self.tree.column("Config", width=600)
        self.tree.column("Actions", width=150, anchor=tk.CENTER)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Bind double-click to show details
        self.tree.bind("<Double-Button-1>", self.on_instance_double_click)
        self.tree.bind("<Button-3>", self.on_instance_right_click)
        
        # Bottom frame: Logs
        log_frame = ttk.LabelFrame(self.root, text="Logs", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, 
                                                  wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure log text tags for colors
        self.log_text.tag_config("stdout", foreground="black")
        self.log_text.tag_config("stderr", foreground="red")
        self.log_text.tag_config("error", foreground="red", font=("Consolas", 9, "bold"))
        self.log_text.tag_config("info", foreground="blue")
        self.log_text.tag_config("timestamp", foreground="gray")
    
    def load_instances(self):
        """Load instances từ config"""
        instances_count = int(self.config.get('INSTANCES', 3))
        
        for i in range(1, instances_count + 1):
            instance = InstanceController(i, self.config, self.workspace, self.python_cmd)
            self.instances.append(instance)
        
        self.refresh_ui()
    
    def refresh_ui(self):
        """Cập nhật UI với trạng thái hiện tại"""
        # Clear treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add instances
        for instance in self.instances:
            status_emoji = {
                "stopped": "⚪",
                "running": "🟢",
                "completed": "✅",
                "failed": "❌"
            }.get(instance.status, "⚪")
            
            env = instance.get_env()
            config_str = (f"📁 {env['COOKIES_FOLDER']} | "
                         f"📝 {env['PROMPT_FILE']} | "
                         f"📐 {env['ASPECT_RATIO']} | "
                         f"💾 {env['OUTPUT_DIR']}")
            
            self.tree.insert("", tk.END, values=(
                f"Worker {instance.instance_id}",
                f"{status_emoji} {instance.status.title()}",
                instance.get_runtime(),
                config_str,
                ""
            ), tags=(instance.instance_id,))
        
        # Update status label
        running_count = sum(1 for i in self.instances if i.status == "running")
        completed_count = sum(1 for i in self.instances if i.status == "completed")
        failed_count = sum(1 for i in self.instances if i.status == "failed")
        
        status_text = f"Running: {running_count} | Completed: {completed_count} | Failed: {failed_count}"
        self.status_label.config(text=status_text)
    
    def on_instance_double_click(self, event):
        """Double click để start/stop instance"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        instance_id = item['tags'][0]
        instance = self.instances[instance_id - 1]
        
        if instance.status == "stopped" or instance.status == "failed":
            self.start_instance(instance_id)
        elif instance.status == "running":
            self.stop_instance(instance_id)
    
    def on_instance_right_click(self, event):
        """Right click menu"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        instance_id = item['tags'][0]
        instance = self.instances[instance_id - 1]
        
        menu = tk.Menu(self.root, tearoff=0)
        
        if instance.status in ["stopped", "failed"]:
            menu.add_command(label="▶️ Start", 
                           command=lambda: self.start_instance(instance_id))
        
        if instance.status == "running":
            menu.add_command(label="⏹️ Stop", 
                           command=lambda: self.stop_instance(instance_id))
        
        menu.add_separator()
        menu.add_command(label="📋 Show Details", 
                        command=lambda: self.show_instance_details(instance_id))
        
        menu.post(event.x_root, event.y_root)
    
    def start_instance(self, instance_id):
        """Start một instance"""
        instance = self.instances[instance_id - 1]
        
        self.log(f"🚀 Starting Worker {instance_id}...", "info")
        
        if instance.start():
            env = instance.get_env()
            self.log(f"   📁 Cookies: {env['COOKIES_FOLDER']}", "info")
            self.log(f"   📝 Prompts: {env['PROMPT_FILE']}", "info")
            self.log(f"   📐 Aspect Ratio: {env['ASPECT_RATIO']}", "info")
            self.log(f"   💾 Output: {env['OUTPUT_DIR']}", "info")
        else:
            self.log(f"❌ Failed to start Worker {instance_id}", "error")
    
    def stop_instance(self, instance_id):
        """Stop một instance"""
        instance = self.instances[instance_id - 1]
        
        if messagebox.askyesno("Confirm", f"Stop Worker {instance_id}?"):
            self.log(f"⏹️ Stopping Worker {instance_id}...", "info")
            instance.stop()
    
    def start_all(self):
        """Start tất cả instances"""
        if not messagebox.askyesno("Confirm", "Start all instances?"):
            return
        
        startup_delay = int(self.config.get('STARTUP_DELAY', 5))
        
        def start_all_thread():
            for i, instance in enumerate(self.instances, 1):
                if instance.status in ["stopped", "failed"]:
                    self.start_instance(i)
                    
                    if i < len(self.instances):
                        self.log(f"⏰ Waiting {startup_delay}s before next instance...", "info")
                        time.sleep(startup_delay)
        
        threading.Thread(target=start_all_thread, daemon=True).start()
    
    def stop_all(self):
        """Stop tất cả instances"""
        if not messagebox.askyesno("Confirm", "Stop all running instances?"):
            return
        
        self.log("⏹️ Stopping all instances...", "info")
        
        for i, instance in enumerate(self.instances, 1):
            if instance.status == "running":
                instance.stop()
    
    def show_instance_details(self, instance_id):
        """Hiển thị chi tiết instance"""
        instance = self.instances[instance_id - 1]
        env = instance.get_env()
        
        details = f"""
Worker {instance_id} Details:
─────────────────────────────
Status: {instance.status.title()}
Runtime: {instance.get_runtime()}

Configuration:
  Cookies: {env['COOKIES_FOLDER']}
  Prompts: {env['PROMPT_FILE']}
  Output: {env['OUTPUT_DIR']}
  Aspect Ratio: {env['ASPECT_RATIO']}
  Image Count: {env['IMAGE_COUNT']}
  Headless: {env['BROWSER_HEADLESS']}

Times:
  Started: {instance.start_time or 'N/A'}
  Ended: {instance.end_time or 'N/A'}
        """
        
        messagebox.showinfo(f"Worker {instance_id}", details)
    
    def clear_logs(self):
        """Xóa logs"""
        self.log_text.delete(1.0, tk.END)
    
    def log(self, message, tag="stdout"):
        """Thêm log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.log_text.insert(tk.END, f"{message}\n", tag)
        self.log_text.see(tk.END)
    
    def start_update_loop(self):
        """Bắt đầu vòng lặp cập nhật UI"""
        self.update_ui()
    
    def update_ui(self):
        """Cập nhật UI định kỳ"""
        # Process log queues
        for instance in self.instances:
            try:
                while True:
                    stream_type, timestamp, message = instance.log_queue.get_nowait()
                    
                    if timestamp:
                        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
                    
                    prefix = f"[Worker {instance.instance_id}] "
                    self.log_text.insert(tk.END, prefix, "info")
                    self.log_text.insert(tk.END, f"{message}\n", stream_type)
                    self.log_text.see(tk.END)
                    
            except queue.Empty:
                break
        
        # Refresh tree
        self.refresh_ui()
        
        # Schedule next update
        self.update_timer = self.root.after(1000, self.update_ui)
    
    def on_closing(self):
        """Handle window closing"""
        running_count = sum(1 for i in self.instances if i.status == "running")
        
        if running_count > 0:
            if not messagebox.askyesno("Confirm Exit", 
                                      f"{running_count} instances are still running.\nStop them and exit?"):
                return
        
        # Stop all instances
        for instance in self.instances:
            if instance.status == "running":
                instance.stop()
        
        # Cancel update timer
        if self.update_timer:
            self.root.after_cancel(self.update_timer)
        
        self.root.destroy()


def main():
    root = tk.Tk()
    app = LauncherGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
