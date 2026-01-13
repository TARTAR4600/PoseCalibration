import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
import subprocess
import os
import threading
import json
from datetime import datetime

class ADBTool:
    def __init__(self, root):
        self.root = root
        self.root.title("ADB 交互工具 - Ai4CityLab (全功能版)")
        self.root.geometry("1250x950")
        
        # 配置文件路径
        self.config_file = "adb_config.json"
        
        # 初始默认设置与历史记录
        self.config = self.load_config()
        self.current_path = self.config.get("last_path", os.getcwd())

        self.create_widgets()

    def load_config(self):
        """加载历史记录和配置"""
        default_config = {
            "ip_history": ["192.168.137.1"],
            "port_history": ["5555"],
            "cmd_history": ["logcat -d > adb_log.txt", "shell pm list packages -3"],
            "pair_history": ["192.168.137.x:port"],
            "pkg_history": [],
            "last_path": os.getcwd(),
            "notes": "在这里粘贴乱七八糟的东西或做笔记..."
        }
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    for key, val in default_config.items():
                        if key not in saved:
                            saved[key] = val
                    return saved
            except:
                return default_config
        return default_config

    def save_config(self):
        """保存当前配置和历史到本地"""
        self.config["last_path"] = self.path_var.get()
        self.config["notes"] = self.notes_area.get("1.0", tk.END).strip()
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def update_history(self, key, value):
        """更新特定的历史记录列表"""
        value = value.strip()
        if not value: return
        
        history = self.config.get(key, [])
        if value in history:
            history.remove(value)
        history.insert(0, value)
        self.config[key] = history[:20]
        
        # 更新对应的下拉框值
        if key == "ip_history": self.ip_combo['values'] = self.config[key]
        elif key == "port_history": self.port_combo['values'] = self.config[key]
        elif key == "cmd_history": self.cmd_combo['values'] = self.config[key]
        elif key == "pair_history": self.pair_addr_combo['values'] = self.config[key]
        elif key == "pkg_history": self.pkg_combo['values'] = self.config[key]
        
        self.save_config()

    def create_widgets(self):
        self.paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=4)
        self.paned.pack(fill="both", expand=True)

        # --- 左侧：操作面板 ---
        self.left_frame = tk.Frame(self.paned)
        self.paned.add(self.left_frame, width=700)

        # --- 右侧：笔记区域 ---
        self.right_frame = tk.Frame(self.paned, padx=10, pady=5)
        self.paned.add(self.right_frame, width=500)

        self.setup_left_panel()
        self.setup_right_panel()

    def setup_left_panel(self):
        container = tk.Frame(self.left_frame)
        container.pack(fill="both", expand=True)

        # 1. 运行路径
        frame_path = tk.LabelFrame(container, text="1. 运行路径", padx=10, pady=5)
        frame_path.pack(fill="x", padx=10, pady=2)
        self.path_var = tk.StringVar(value=self.current_path)
        tk.Entry(frame_path, textvariable=self.path_var).pack(side="left", fill="x", expand=True)
        tk.Button(frame_path, text="浏览", command=self.select_path).pack(side="right", padx=5)

        # 2. 网络工具
        frame_quick = tk.LabelFrame(container, text="2. 网络工具", padx=10, pady=5)
        frame_quick.pack(fill="x", padx=10, pady=2)
        tk.Button(frame_quick, text="打开/关闭计算机移动热点设置", command=self.open_hotspot_settings, bg="#fff9c4").pack(fill="x")

        # 3. WLAN 配对
        frame_pair = tk.LabelFrame(container, text="3. WLAN 配对 (Android 11+)", padx=10, pady=5)
        frame_pair.pack(fill="x", padx=10, pady=2)
        tk.Label(frame_pair, text="地址:").grid(row=0, column=0)
        self.pair_addr_combo = ttk.Combobox(frame_pair, values=self.config["pair_history"], width=25)
        self.pair_addr_combo.grid(row=0, column=1, padx=5)
        if self.config["pair_history"]: self.pair_addr_combo.set(self.config["pair_history"][0])
        tk.Label(frame_pair, text="码:").grid(row=0, column=2)
        self.pair_code = tk.Entry(frame_pair, width=10)
        self.pair_code.grid(row=0, column=3, padx=5)
        tk.Button(frame_pair, text="配对", command=self.adb_pair, bg="#e8f5e9").grid(row=0, column=4, padx=5)

        # 4. WLAN 连接
        frame_conn = tk.LabelFrame(container, text="4. 通过 WLAN 连接 (adb connect)", padx=10, pady=5)
        frame_conn.pack(fill="x", padx=10, pady=2)
        tk.Label(frame_conn, text="IP:").pack(side="left")
        self.ip_combo = ttk.Combobox(frame_conn, values=self.config["ip_history"], width=15)
        self.ip_combo.pack(side="left", padx=2)
        if self.config["ip_history"]: self.ip_combo.set(self.config["ip_history"][0])
        tk.Label(frame_conn, text="端口:").pack(side="left")
        self.port_combo = ttk.Combobox(frame_conn, values=self.config["port_history"], width=8)
        self.port_combo.pack(side="left", padx=2)
        if self.config["port_history"]: self.port_combo.set(self.config["port_history"][0])
        tk.Button(frame_conn, text="连接", command=self.adb_connect, bg="#e3f2fd").pack(side="left", padx=5)

        # 5. 设备管理 (新增投屏按钮)
        frame_device = tk.LabelFrame(container, text="5. 设备管理 & 开发者投屏", padx=10, pady=5)
        frame_device.pack(fill="x", padx=10, pady=2)
        tk.Button(frame_device, text="刷新列表", command=self.adb_devices).pack(side="left", padx=5)
        tk.Button(frame_device, text="无线投屏 (scrcpy)", command=self.start_mirroring, bg="#d1c4e9", font=("微软雅黑", 9, "bold")).pack(side="left", padx=20)
        tk.Button(frame_device, text="断开所有", command=self.adb_disconnect, fg="red").pack(side="right", padx=5)

        # 6. 自定义命令
        frame_log = tk.LabelFrame(container, text="6. 自定义命令", padx=10, pady=5)
        frame_log.pack(fill="x", padx=10, pady=2)
        tk.Label(frame_log, text="adb").pack(side="left")
        self.cmd_combo = ttk.Combobox(frame_log, values=self.config["cmd_history"])
        self.cmd_combo.pack(side="left", fill="x", expand=True, padx=5)
        if self.config["cmd_history"]: self.cmd_combo.set(self.config["cmd_history"][0])
        tk.Button(frame_log, text="执行", command=self.run_custom, bg="#f3e5f5").pack(side="right")

        # 7. 应用管理
        frame_app = tk.LabelFrame(container, text="7. 应用管理", padx=10, pady=5)
        frame_app.pack(fill="x", padx=10, pady=2)
        install_row = tk.Frame(frame_app)
        install_row.pack(fill="x", pady=2)
        self.apk_path_var = tk.StringVar()
        tk.Entry(install_row, textvariable=self.apk_path_var, state="readonly").pack(side="left", fill="x", expand=True)
        tk.Button(install_row, text="选择APK", command=self.select_apk).pack(side="left", padx=2)
        tk.Button(install_row, text="安装", command=self.adb_install, bg="#e0f2f1").pack(side="left", padx=2)
        pkg_row = tk.Frame(frame_app)
        pkg_row.pack(fill="x", pady=2)
        self.pkg_combo = ttk.Combobox(pkg_row, values=self.config["pkg_history"], width=30)
        self.pkg_combo.pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(pkg_row, text="找第三方包", command=self.list_third_party_packages, font=("微软雅黑", 8)).pack(side="left", padx=2)
        tk.Button(pkg_row, text="卸载", command=self.adb_uninstall, fg="red").pack(side="left", padx=2)

        # 控制台
        console_header = tk.Frame(container)
        console_header.pack(fill="x", padx=10, pady=(5, 0))
        tk.Label(console_header, text="日志输出:", font=("微软雅黑", 9, "bold")).pack(side="left")
        tk.Button(console_header, text="导出", command=self.export_console_log, font=("微软雅黑", 8)).pack(side="right", padx=2)
        tk.Button(console_header, text="清空", command=self.clear_console_log, font=("微软雅黑", 8)).pack(side="right", padx=2)
        self.console = scrolledtext.ScrolledText(container, height=18, bg="#263238", fg="#80df83", font=("Consolas", 10))
        self.console.pack(fill="both", padx=10, pady=5, expand=True)

    def setup_right_panel(self):
        tk.Label(self.right_frame, text="随手记 / 调试笔记:", font=("微软雅黑", 10, "bold")).pack(anchor="w")
        self.notes_area = scrolledtext.ScrolledText(self.right_frame, bg="#fffde7", font=("微软雅黑", 10), undo=True)
        self.notes_area.pack(fill="both", expand=True, pady=5)
        self.notes_area.insert("1.0", self.config.get("notes", ""))

    # --- 功能逻辑 ---

    def log(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.insert(tk.END, f"[{timestamp}] > {text}\n")
        self.console.see(tk.END)

    def start_mirroring(self):
        """核心功能：无线投屏"""
        def target():
            self.log("正在尝试启动无线投屏 (scrcpy)...")
            # 检查是否有设备连接
            check = subprocess.run("adb devices", capture_output=True, text=True, shell=True)
            if "device" not in check.stdout.split('\n')[1]:
                self.log("[错误] 没有检测到已连接的设备，请先完成第4步连接。")
                return
            
            # 启动 scrcpy
            # --always-on-top: 窗口置顶，方便调试
            # --window-title: 方便识别
            cmd = "scrcpy --always-on-top --window-title 'Ai4CityLab Mirror'"
            try:
                # 使用 Popen 不阻塞 UI
                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                self.log("scrcpy 已启动。若未弹出窗口，请确保已安装 scrcpy 并加入环境变量。")
                # 持续读取错误流，防止静默失败
                _, stderr = proc.communicate()
                if stderr and "error" in stderr.lower():
                    self.log(f"[scrcpy 报错]: {stderr.strip()}")
            except FileNotFoundError:
                self.log("[错误] 未找到 scrcpy 执行文件。请从 GitHub 下载并添加至 PATH。")

        threading.Thread(target=target, daemon=True).start()

    def select_path(self):
        path = filedialog.askdirectory()
        if path: self.path_var.set(path); self.save_config()

    def select_apk(self):
        file_path = filedialog.askopenfilename(filetypes=[("APK files", "*.apk"), ("All files", "*.*")])
        if file_path: self.apk_path_var.set(file_path)

    def open_hotspot_settings(self):
        subprocess.Popen("start ms-settings:network-mobilehotspot", shell=True)

    def clear_console_log(self):
        self.console.delete("1.0", tk.END)

    def run_command(self, cmd, update_key=None, update_val=None):
        cwd = self.path_var.get() or None
        def target():
            self.log(f"执行: {cmd}")
            if update_key and update_val: self.update_history(update_key, update_val)
            try:
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd)
                stdout, stderr = process.communicate()
                if stdout: self.log(stdout.strip())
                if stderr: self.log(f"[ERROR]: {stderr.strip()}")
            except Exception as e: self.log(f"[EXCEPTION]: {str(e)}")
        threading.Thread(target=target, daemon=True).start()

    def adb_pair(self):
        addr, code = self.pair_addr_combo.get(), self.pair_code.get()
        if addr and code: self.run_command(f"adb pair {addr} {code}", "pair_history", addr)

    def adb_connect(self):
        ip, port = self.ip_combo.get(), self.port_combo.get()
        if ip and port: self.run_command(f"adb connect {ip}:{port}", "ip_history", ip); self.update_history("port_history", port)

    def adb_devices(self): self.run_command("adb devices")
    def adb_disconnect(self): self.run_command("adb disconnect")
    def adb_install(self):
        apk = self.apk_path_var.get()
        if apk: self.run_command(f'adb install -r "{apk}"')
    def list_third_party_packages(self): self.run_command('adb shell pm list packages -3')
    def adb_uninstall(self):
        pkg = self.pkg_combo.get().strip()
        if pkg: self.run_command(f'adb uninstall {pkg}', "pkg_history", pkg)
    def run_custom(self):
        cmd = self.cmd_combo.get().strip()
        if cmd: self.run_command(f"adb {cmd}" if not cmd.startswith("adb") else cmd, "cmd_history", cmd)
    def export_console_log(self):
        content = self.console.get("1.0", tk.END).strip()
        fp = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=f"adb_log_{datetime.now().strftime('%m%d_%H%M')}.txt")
        if fp: 
            with open(fp, "w", encoding="utf-8") as f: f.write(content)

if __name__ == "__main__":
    root = tk.Tk()
    app = ADBTool(root)
    root.protocol("WM_DELETE_WINDOW", lambda: [app.save_config(), root.destroy()])
    root.mainloop()