import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
import time
import json

from Client_Application import client_application

class ClientGUI:


    def __init__(self, root):

        self.root = root
        self.root.title("Chat Client")
        self.root.geometry("900x600")

        self.client = None
        self.server_ip = "127.0.0.1"
        self.server_port = 12000

        self.gui_queue = queue.Queue()

        self.mode = "LOGIN"
        self.chat_target = None
        self.group_name = None

        self.build_layout()

        self.root.after(100, self.process_gui_queue)

    def build_layout(self):

        self.left_panel = tk.Frame(self.root, width=200)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y)

        self.center_panel = tk.Frame(self.root)
        self.center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.right_panel = tk.Frame(self.root, width=200)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y)

        self.chat_display = tk.Text(self.center_panel, state="disabled")
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        bottom = tk.Frame(self.center_panel)
        bottom.pack(fill=tk.X)

        self.message_entry = tk.Entry(bottom)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        send_btn = tk.Button(bottom, text="Send", command=self.send_message)
        send_btn.pack(side=tk.LEFT, padx=5)

        file_btn = tk.Button(bottom, text="Send File", command=self.send_file)
        file_btn.pack(side=tk.LEFT, padx=5)

        self.build_login_menu()

    def clear_panel(self, panel):
        for w in panel.winfo_children():
            w.destroy()

    def build_login_menu(self):

        self.clear_panel(self.left_panel)

        tk.Label(self.left_panel, text="Server IP").pack(pady=5)
        self.ip_entry = tk.Entry(self.left_panel)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack()

        tk.Label(self.left_panel, text="Username").pack(pady=5)
        self.username_entry = tk.Entry(self.left_panel)
        self.username_entry.pack()

        tk.Label(self.left_panel, text="Password").pack(pady=5)
        self.password_entry = tk.Entry(self.left_panel, show="*")
        self.password_entry.pack()

        tk.Button(self.left_panel, text="Login", command=self.login).pack(pady=5)
        tk.Button(self.left_panel, text="Register", command=self.register).pack(pady=5)

    def build_main_menu(self):

        self.clear_panel(self.left_panel)

        tk.Label(self.left_panel, text="Actions", font=("Arial", 12, "bold")).pack(pady=10)

        tk.Button(self.left_panel, text="1-on-1 Chat", command=self.start_private_chat).pack(fill=tk.X)
        tk.Button(self.left_panel, text="Create Group", command=self.create_group).pack(fill=tk.X)
        tk.Button(self.left_panel, text="Join Group", command=self.join_group).pack(fill=tk.X)
        tk.Button(self.left_panel, text="View Online Users", command=self.view_online).pack(fill=tk.X)
        tk.Button(self.left_panel, text="Logout", command=self.logout).pack(fill=tk.X)

        tk.Label(self.right_panel, text="Online Users").pack()
        self.user_list = tk.Listbox(self.right_panel)
        self.user_list.pack(fill=tk.BOTH, expand=True)

    def append_chat(self, text):

        self.chat_display.configure(state="normal")
        self.chat_display.insert(tk.END, text + "\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see(tk.END)

    def login(self):

        username = self.username_entry.get()
        password = self.password_entry.get()
        self.server_ip = self.ip_entry.get()

        self.client = client_application(username)

        self.client.tcp_connect(self.server_ip, self.server_port)
        self.client.udp_connect(self.server_ip, self.server_port)

        self.patch_receive_method()

        login_message = self.client.send_command(
            "LOGIN",
            {"username": username, "password": password}
        )

        self.client.send_message_tcp(login_message)

        time.sleep(1)

        self.mode = "MENU"
        self.build_main_menu()

    def register(self):

        username = self.username_entry.get()
        password = self.password_entry.get()
        self.server_ip = self.ip_entry.get()

        self.client = client_application(username)

        self.client.tcp_connect(self.server_ip, self.server_port)
        self.client.udp_connect(self.server_ip, self.server_port)

        self.patch_receive_method()

        register_message = self.client.send_command(
            "REGISTER",
            {"username": username, "password": password}
        )

        self.client.send_message_tcp(register_message)

        messagebox.showinfo("Register", "Registration request sent")

    def start_private_chat(self):

        target = tk.simpledialog.askstring("User", "Enter username")

        if not target:
            return

        self.mode = "PRIVATE"
        self.chat_target = target

        if not self.client.listener_started:
            threading.Thread(target=self.client.start_peer_listener, daemon=True).start()
            time.sleep(0.5)

        connect_request_message = self.client.send_command(
            "CONNECT_REQUEST",
            {"target_user": target}
        )

        self.client.send_message_tcp(connect_request_message)

        threading.Thread(target=self.wait_for_peer, daemon=True).start()

    def wait_for_peer(self):

        connected = self.client.get_connect_message_for_peer()

        if connected:
            self.gui_queue.put(("chat", "Connected to peer"))
        else:
            self.gui_queue.put(("chat", "Connection failed"))

    def create_group(self):

        name = tk.simpledialog.askstring("Group", "Group Name")

        if not name:
            return

        members = tk.simpledialog.askstring("Members", "Comma separated usernames")

        if members:
            members = [m.strip() for m in members.split(",")]
        else:
            members = []

        message = self.client.send_command(
            "CREATE",
            {"user": self.client.username, "group-name": name, "members": members}
        )

        self.client.send_message_tcp(message)

        self.mode = "GROUP"
        self.group_name = name

        self.append_chat(f"Created group {name}")

    def join_group(self):

        name = tk.simpledialog.askstring("Join", "Group name")

        if not name:
            return

        message = self.client.send_command(
            "JOIN",
            {"user": self.client.username, "group-name": name}
        )

        self.client.send_message_tcp(message)

        self.mode = "GROUP"
        self.group_name = name

        self.append_chat(f"Joined group {name}")

    def send_message(self):

        msg = self.message_entry.get()

        if not msg:
            return

        if self.mode == "PRIVATE":

            data_message = self.client.send_data(
                "SEND_TEXT",
                {"message": msg}
            )

            ok = self.client.send_message_peer(data_message)

            if ok:
                self.append_chat("You: " + msg)

        elif self.mode == "GROUP":

            gmessage = self.client.send_data(
                "GTEXT_MESSAGE",
                {"user": self.client.username, "group-name": self.group_name, "message": msg}
            )

            self.client.send_message_tcp(gmessage)

            self.append_chat("You: " + msg)

        self.message_entry.delete(0, tk.END)

    def send_file(self):

        path = filedialog.askopenfilename()

        if not path:
            return

        filetype = tk.simpledialog.askstring("File type", "images / audio / videos / documents / other")

        if self.mode == "PRIVATE":
            self.client.send_file(path, filetype, self.chat_target)

        elif self.mode == "GROUP":
            self.client.send_file(path, filetype, self.group_name)

    def view_online(self):

        request = self.client.send_command("VIEW_ONLINE", "")
        self.client.send_message_tcp(request)

    def logout(self):

        logout_message = self.client.send_command("LOGOUT", "")
        self.client.send_message_tcp(logout_message)

        self.client.close_connection()

        self.mode = "LOGIN"
        self.build_login_menu()

    def patch_receive_method(self):

        original_receive = self.client.receive_message

        def new_receive(message):

            try:
                data = json.loads(message)
            except:
                return

            header = data.get("header", {})
            body = data.get("body", {})

            cmd = header.get("command")

            if cmd == "SEND_TEXT":
                self.gui_queue.put(("chat", body.get("message", "")))

            elif cmd == "GTEXT_MESSAGE":
                user = header.get("senderId", "")
                msg = body.get("message", "")
                self.gui_queue.put(("chat", f"{user}: {msg}"))

            elif cmd == "VIEW_ONLINE":
                users = body.get("users", [])
                self.gui_queue.put(("users", users))

            else:
                original_receive(message)

        self.client.receive_message = new_receive

    def process_gui_queue(self):

        try:
            while True:

                item = self.gui_queue.get_nowait()

                if item[0] == "chat":
                    self.append_chat(item[1])

                elif item[0] == "users":

                    self.user_list.delete(0, tk.END)

                    for u in item[1]:
                        self.user_list.insert(tk.END, u)

        except queue.Empty:
            pass

        self.root.after(100, self.process_gui_queue)
    

if __name__ == "__main__":


    root = tk.Tk()

    app = ClientGUI(root)

    root.mainloop()


''''
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import time

from Client_Application import client_application   # import your client class


class ClientGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Chat Client")

        self.client = None
        self.server_ip = "127.0.0.1"
        self.server_port = 12000

        self.build_login_screen()

    # -----------------------------
    # LOGIN / REGISTER SCREEN
    # -----------------------------
    def build_login_screen(self):

        self.clear_window()

        tk.Label(self.root, text="Server IP").pack()
        self.ip_entry = tk.Entry(self.root)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack()

        tk.Label(self.root, text="Username").pack()
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack()

        tk.Label(self.root, text="Password").pack()
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack()

        tk.Button(self.root, text="Login", command=self.login).pack(pady=5)
        tk.Button(self.root, text="Register", command=self.register).pack(pady=5)

    # -----------------------------
    # MAIN MENU
    # -----------------------------
    def build_main_menu(self):

        self.clear_window()

        tk.Label(self.root, text=f"Logged in as {self.client.username}").pack()

        tk.Button(self.root, text="1-on-1 Chat", command=self.open_chat_window).pack(pady=5)
        tk.Button(self.root, text="View Online Users", command=self.view_online).pack(pady=5)
        tk.Button(self.root, text="Logout", command=self.logout).pack(pady=5)

    # -----------------------------
    # CHAT WINDOW
    # -----------------------------
    def open_chat_window(self):

        chat_window = tk.Toplevel(self.root)
        chat_window.title("Chat")

        self.chat_display = scrolledtext.ScrolledText(chat_window, width=60, height=20)
        self.chat_display.pack()

        self.message_entry = tk.Entry(chat_window, width=40)
        self.message_entry.pack(side=tk.LEFT, padx=5)

        send_btn = tk.Button(chat_window, text="Send", command=self.send_message)
        send_btn.pack(side=tk.LEFT)

        tk.Button(chat_window, text="Connect User", command=self.request_peer).pack()

    # -----------------------------
    # NETWORK ACTIONS
    # -----------------------------
    def login(self):

        username = self.username_entry.get()
        password = self.password_entry.get()
        self.server_ip = self.ip_entry.get()

        self.client = client_application(username)

        self.client.tcp_connect(self.server_ip, self.server_port)
        self.client.udp_connect(self.server_ip, self.server_port)

        login_message = self.client.send_command(
            "LOGIN",
            {"username": username, "password": password}
        )

        self.client.send_message_tcp(login_message)

        time.sleep(1)

        self.build_main_menu()

    def register(self):

        username = self.username_entry.get()
        password = self.password_entry.get()
        self.server_ip = self.ip_entry.get()

        self.client = client_application(username)

        self.client.tcp_connect(self.server_ip, self.server_port)
        self.client.udp_connect(self.server_ip, self.server_port)

        register_message = self.client.send_command(
            "REGISTER",
            {"username": username, "password": password}
        )

        self.client.send_message_tcp(register_message)

        messagebox.showinfo("Register", "Registration request sent")

    def request_peer(self):

        target = tk.simpledialog.askstring("Chat", "Enter username")

        if not target:
            return

        if not self.client.listener_started:
            threading.Thread(target=self.client.start_peer_listener, daemon=True).start()
            time.sleep(0.5)

        connect_request_message = self.client.send_command(
            "CONNECT_REQUEST",
            {"target_user": target}
        )

        self.client.send_message_tcp(connect_request_message)

        threading.Thread(target=self.wait_for_peer, daemon=True).start()

    def wait_for_peer(self):

        connected = self.client.get_connect_message_for_peer()

        if connected:
            self.chat_display.insert(tk.END, "Connected to peer\n")
        else:
            self.chat_display.insert(tk.END, "Connection failed\n")

    def send_message(self):

        msg = self.message_entry.get()

        if not msg:
            return

        data_message = self.client.send_data(
            "SEND_TEXT",
            {"message": msg}
        )

        sent = self.client.send_message_peer(data_message)

        if sent:
            self.chat_display.insert(tk.END, f"You: {msg}\n")

        self.message_entry.delete(0, tk.END)

    def view_online(self):

        request_message = self.client.send_command("VIEW_ONLINE", "")
        self.client.send_message_tcp(request_message)

    def logout(self):

        logout_message = self.client.send_command("LOGOUT", "")
        self.client.send_message_tcp(logout_message)

        self.client.close_connection()

        self.build_login_screen()

    # -----------------------------
    # UTIL
    # -----------------------------
    def clear_window(self):

        for widget in self.root.winfo_children():
            widget.destroy()


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":


    root = tk.Tk()
    root.geometry("400x300")

    app = ClientGUI(root)

    root.mainloop()
    '''