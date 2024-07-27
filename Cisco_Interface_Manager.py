import tkinter as tk
from tkinter import ttk
from netmiko import ConnectHandler
import json
import os
import time
import threading

config_file = "running_config.json"
command_history = []

class ConnectionTimer:
    def __init__(self, label):
        self.label = label
        self.start_time = None
        self.running = False
        self.thread = None

    def start(self):
        self.start_time = time.time()
        self.running = True
        self.thread = threading.Thread(target=self.update)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread is not None:
            self.thread.join()

    def update(self):
        while self.running:
            elapsed_time = int(time.time() - self.start_time)
            minutes, seconds = divmod(elapsed_time, 60)
            hours, minutes = divmod(minutes, 60)
            time_format = f"{hours:02}:{minutes:02}:{seconds:02}"
            self.label.config(text=time_format)
            time.sleep(1)

def save_running_config():
    with open(config_file, 'w') as f:
        json.dump(command_history, f)

def load_running_config():
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return []

def connect_device():
    global net_connect
    device = {
        "device_type": "cisco_ios",
        "host": host_entry.get(),
        "username": username_entry.get(),
        "password": password_entry.get(),
        "secret": secret_entry.get(),
    }
    
    try:
        net_connect = ConnectHandler(**device)
        net_connect.enable()
        update_status(f"Connected to {host_entry.get()}")
        update_connection_status(True)
        connection_timer.start()
        populate_interfaces_and_vlans()
        populate_port_status()
        apply_stored_config()
    except Exception as e:
        update_status(f"An error occurred: {e}")
        update_connection_status(False)

def apply_stored_config():
    global command_history
    command_history = load_running_config()
    if command_history:
        for command_set in command_history:
            net_connect.send_config_set(command_set)

def disconnect_device():
    try:
        net_connect.disconnect()
        update_status(f"Disconnected from {host_entry.get()}")
        update_connection_status(False)
        connection_timer.stop()
    except Exception as e:
        update_status(f"An error occurred: {e}")
        update_connection_status(False)

def update_connection_status(connected):
    if connected:
        connection_status_label.config(text="●", fg="green")
    else:
        connection_status_label.config(text="●", fg="red")
        connection_timer_label.config(text="00:00:00")

def save_input():
    new_data = {
        "host": host_entry.get(),
        "username": username_entry.get(),
        "password": password_entry.get(),
        "secret": secret_entry.get()
    }
    
    if os.path.exists('saved_inputs.json'):
        with open('saved_inputs.json', 'r') as f:
            saved_inputs = json.load(f)
    else:
        saved_inputs = []

    # Check for duplicate host
    for data in saved_inputs:
        if data['host'] == new_data['host']:
            update_status("Host already exists. Duplicate not allowed.")
            return
    
    saved_inputs.append(new_data)
    
    with open('saved_inputs.json', 'w') as f:
        json.dump(saved_inputs, f, indent=4)
    
    update_status("Saved successfully.")
    save_running_config()

def load_saved_inputs():
    if os.path.exists('saved_inputs.json'):
        with open('saved_inputs.json', 'r') as f:
            saved_inputs = json.load(f)
    else:
        saved_inputs = []
    
    popup = tk.Toplevel()
    popup.title("Saved Hosts")

    # Dynamically set the window size based on the number of saved inputs
    window_height = min(400, 50 + len(saved_inputs) * 30)
    popup.geometry(f"300x{window_height}")

    for widget in popup.winfo_children():
        widget.destroy()
    
    for data in saved_inputs:
        host = data['host']
        button_frame = tk.Frame(popup)
        button_frame.pack(fill='x', padx=5, pady=2)
        button = tk.Button(button_frame, text=f"{host}", command=lambda data=data: load_input(data, popup), relief='flat')
        button.pack(side='left', fill='x', expand=True)
        delete_button = tk.Button(button_frame, text="X", command=lambda host=host: delete_input(host, popup), fg="red", relief='flat')
        delete_button.pack(side='left')

def load_input(data, popup):
    host_entry.delete(0, tk.END)
    host_entry.insert(0, data['host'])
    username_entry.delete(0, tk.END)
    username_entry.insert(0, data['username'])
    password_entry.delete(0, tk.END)
    password_entry.insert(0, data['password'])
    secret_entry.delete(0, tk.END)
    secret_entry.insert(0, data['secret'])
    popup.destroy()

def delete_input(host, popup):
    if os.path.exists('saved_inputs.json'):
        with open('saved_inputs.json', 'r') as f:
            saved_inputs = json.load(f)
        
        saved_inputs = [data for data in saved_inputs if data['host'] != host]
        
        with open('saved_inputs.json', 'w') as f:
            json.dump(saved_inputs, f, indent=4)
    
    popup.destroy()
    load_saved_inputs()

def create_vlan():
    if not net_connect:
        update_status("Not connected to any device.")
        return
    
    vlan_name = vlan_name_entry.get()
    vlan_number = vlan_number_entry.get()
    
    try:
        commands = [
            f"vlan {vlan_number}",
            f"name {vlan_name}",
            "write memory"
        ]
        net_connect.send_config_set(commands)
        command_history.append(commands)
        save_running_config()
        update_status(f"VLAN {vlan_number} named {vlan_name} created successfully.")
    except Exception as e:
        update_status(f"An error occurred: {e}")

def assign_vlan():
    if not net_connect:
        update_status("Not connected to any device.")
        return
    
    interface = interface_combobox.get()
    mode = mode_combobox.get()
    vlan = vlan_combobox.get()
    
    try:
        commands = [
            f"interface {interface}",
            f"switchport trunk encapsulation dot1q" if mode == "trunk" else "",
            f"switchport mode {mode}",
            f"switchport { 'access vlan' if mode == 'access' else 'trunk allowed vlan' } {vlan}",
            "write memory"
        ]
        net_connect.send_config_set([cmd for cmd in commands if cmd])  # Filter out empty commands
        command_history.append([cmd for cmd in commands if cmd])
        save_running_config()
        update_status(f"Assigned VLAN {vlan} to interface {interface} in {mode} mode.")
    except Exception as e:
        update_status(f"An error occurred: {e}")

def assign_native_vlan():
    if not net_connect:
        update_status("Not connected to any device.")
        return
    
    interface = native_interface_combobox.get()
    native_vlan = native_vlan_entry.get()
    
    try:
        commands = [
            f"interface {interface}",
            f"switchport trunk native vlan {native_vlan}",
            "write memory"
        ]
        net_connect.send_config_set(commands)
        command_history.append(commands)
        save_running_config()
        update_status(f"Assigned native VLAN {native_vlan} to interface {interface}.")
    except Exception as e:
        update_status(f"An error occurred: {e}")

def show_interface_status():
    if not net_connect:
        update_status("Not connected to any device.")
        return
    
    interface = status_interface_combobox.get()
    command = f"show interfaces {interface} switchport" if interface else vlan_details_combobox.get()
    
    try:
        output = net_connect.send_command(command)
        show_output_popup(output)
    except Exception as e:
        update_status(f"An error occurred: {e}")

def monitor_traffic():
    if not net_connect:
        update_status("Not connected to any device.")
        return

    command = "show interfaces counters"
    
    try:
        output = net_connect.send_command(command)
        show_output_popup(output)
    except Exception as e:
        update_status(f"An error occurred: {e}")

def show_output_popup(output):
    popup = tk.Toplevel()
    popup.title("Output")
    text = tk.Text(popup, wrap='word')
    text.insert(tk.END, output)
    text.pack(expand=True, fill='both')
    text.config(state=tk.DISABLED)

def populate_interfaces_and_vlans():
    try:
        interfaces_output = net_connect.send_command('show ip interface brief')
        vlans_output = net_connect.send_command('show vlan brief')

        interfaces = [line.split()[0] for line in interfaces_output.splitlines() if len(line.split()) > 0 and 'Interface' not in line]
        vlans = [line.split()[0] for line in vlans_output.splitlines() if len(line.split()) > 0 and line.split()[0].isdigit()]

        interface_combobox['values'] = interfaces
        native_interface_combobox['values'] = interfaces
        status_interface_combobox['values'] = interfaces
        port_security_interface_combobox['values'] = interfaces
        port_speed_interface_combobox['values'] = interfaces
        vlan_combobox['values'] = vlans
    except Exception as e:
        update_status(f"An error occurred while fetching interfaces and VLANs: {e}")

def populate_port_status():
    if not net_connect:
        update_status("Not connected to any device.")
        return
    
    try:
        interfaces_output = net_connect.send_command('show ip interface brief')
        interfaces = []
        for line in interfaces_output.splitlines():
            if 'Interface' in line:
                continue
            parts = line.split()
            if len(parts) > 0:
                interfaces.append((parts[0], parts[4]))  # Interface and Status
        
        for widget in port_symbols_frame.winfo_children():
            widget.destroy()
        
        for interface, status in interfaces:
            port_container = tk.Frame(port_symbols_frame)
            port_container.pack(side='left', padx=0)

            color = '#00ff00' if status == 'up' else '#ff0000'
            port_label = tk.Label(port_container, text="■", fg=color, font=("Arial", 40))
            port_label.pack(side='top', padx=0)
            port_label.bind("<Enter>", lambda e, intf=interface, stat=status: show_tooltip(e, intf, stat))
            port_label.bind("<Leave>", hide_tooltip)
            port_label.bind("<Double-1>", lambda e, intf=interface, lbl=port_label: toggle_port(e, intf, lbl))

            short_interface_name = interface.replace("Ethernet", "e")
            port_text_label = tk.Label(port_container, text=short_interface_name, font=("Arial", 8))  # Reduced font size
            port_text_label.pack(side='top', pady=0)  # Reduced padding
        
    except Exception as e:
        update_status(f"An error occurred while fetching port status: {e}")

def toggle_port(event, interface, label):
    try:
        current_color = label.cget("fg")
        if current_color == "#00ff00":  # Port is up
            commands = [f"interface {interface}", "shutdown", "write memory"]
            net_connect.send_config_set(commands)
            command_history.append(commands)
            label.config(fg="#ff0000")
            update_status(f"Port {interface} has been shut down.")
        else:  # Port is down
            commands = [f"interface {interface}", "no shutdown", "write memory"]
            net_connect.send_config_set(commands)
            command_history.append(commands)
            label.config(fg="#00ff00")
            update_status(f"Port {interface} has been brought up.")
        save_running_config()
    except Exception as e:
        update_status(f"An error occurred: {e}")

def show_tooltip(event, interface, status):
    tooltip = tk.Toplevel()
    tooltip.wm_overrideredirect(True)
    tooltip.geometry(f"+{event.x_root+10}+{event.y_root+10}")
    label = tk.Label(tooltip, text=f"{interface}: {status}", background="yellow", relief='solid', borderwidth=1, font=("Arial", "10", "normal"))
    label.pack()
    event.widget.tooltip = tooltip

def hide_tooltip(event):
    if hasattr(event.widget, 'tooltip'):
        event.widget.tooltip.destroy()

def update_status(message):
    status_label.config(text=message)

def on_port_security_type_change(event):
    input_label.pack_forget()
    input_entry.pack_forget()
    input_combobox.pack_forget()
    note_label.pack_forget()

    selected_type = port_security_type_combobox.get()
    
    if selected_type == "violation":
        input_label.config(text="Input:")
        input_label.pack(side='left', padx=5)
        input_combobox['values'] = ["protect", "restrict", "shutdown"]
        input_combobox.pack(side='left', padx=5)
    elif selected_type == "mac address":
        input_label.config(text="Input:")
        input_label.pack(side='left', padx=5)
        input_entry.pack(side='left', padx=5)
        note_label.config(text="Enter MAC Address")
        note_label.pack(side='left', padx=5)
    elif selected_type == "maximum":
        input_label.config(text="Input:")
        input_label.pack(side='left', padx=5)
        input_entry.pack(side='left', padx=5)
        note_label.config(text="Enter Number")
        note_label.pack(side='left', padx=5)
    elif selected_type == "aging time":
        input_label.config(text="Input:")
        input_label.pack(side='left', padx=5)
        input_entry.pack(side='left', padx=5)
        note_label.config(text="Enter Time")
        note_label.pack(side='left', padx=5)
    elif selected_type == "aging type":
        input_label.config(text="Input:")
        input_label.pack(side='left', padx=5)
        input_combobox['values'] = ["absolute", "inactivity"]
        input_combobox.pack(side='left', padx=5)

def apply_port_security():
    if not net_connect:
        update_status("Not connected to any device.")
        return

    interface = port_security_interface_combobox.get()
    security_type = port_security_type_combobox.get()
    input_value = input_combobox.get() if security_type in ["violation", "aging type"] else input_entry.get()
    
    try:
        commands = [f"interface {interface}"]
        if security_type == "maximum":
            commands.append(f"switchport port-security maximum {input_value}")
        elif security_type == "violation":
            commands.append(f"switchport port-security violation {input_value}")
        elif security_type == "mac address":
            commands.append(f"switchport port-security mac-address {input_value}")
        elif security_type == "aging time":
            commands.append(f"switchport port-security aging time {input_value}")
        elif security_type == "aging type":
            commands.append(f"switchport port-security aging type {input_value}")
        
        commands.append("write memory")
        net_connect.send_config_set(commands)
        command_history.append(commands)
        save_running_config()
        update_status(f"Applied port security settings to {interface}.")
    except Exception as e:
        update_status(f"An error occurred: {e}")

def set_port_speed_duplex():
    if not net_connect:
        update_status("Not connected to any device.")
        return

    interface = port_speed_interface_combobox.get()
    speed = port_speed_combobox.get()
    duplex = port_duplex_combobox.get()

    try:
        commands = [f"interface {interface}"]
        if speed:
            commands.append(f"speed {speed}")
        if duplex:
            commands.append(f"duplex {duplex}")
        commands.append("write memory")
        
        net_connect.send_config_set(commands)
        command_history.append(commands)
        save_running_config()
        update_status(f"Set speed and duplex for {interface}.")
    except Exception as e:
        update_status(f"An error occurred: {e}")

# Create the main window
root = tk.Tk()
root.title("Cisco Command Executor")
root.geometry("800x600")  # Increased window size

# Create a Notebook widget for tabs
notebook = ttk.Notebook(root)
notebook.pack(pady=10, expand=True, fill='both')

# Create frames for each tab
frame_connection = ttk.Frame(notebook)
frame_vlan = ttk.Frame(notebook)
frame_port = ttk.Frame(notebook)

frame_connection.pack(fill='both', expand=True)
frame_vlan.pack(fill='both', expand=True)
frame_port.pack(fill='both', expand=True)

# Add frames to notebook
notebook.add(frame_connection, text='Connection')
notebook.add(frame_vlan, text='VLAN')
notebook.add(frame_port, text='Port Management')

# Connection tab widgets
tk.Label(frame_connection, text="Host:").grid(row=0, column=0, padx=10, pady=5, sticky='w')
host_entry = tk.Entry(frame_connection)
host_entry.grid(row=0, column=1, padx=10, pady=5, sticky='w')

tk.Label(frame_connection, text="Username:").grid(row=1, column=0, padx=10, pady=5, sticky='w')
username_entry = tk.Entry(frame_connection)
username_entry.grid(row=1, column=1, padx=10, pady=5, sticky='w')

tk.Label(frame_connection, text="Password:").grid(row=2, column=0, padx=10, pady=5, sticky='w')
password_entry = tk.Entry(frame_connection, show='*')
password_entry.grid(row=2, column=1, padx=10, pady=5, sticky='w')

tk.Label(frame_connection, text="Secret:").grid(row=3, column=0, padx=10, pady=5, sticky='w')
secret_entry = tk.Entry(frame_connection, show='*')
secret_entry.grid(row=3, column=1, padx=10, pady=5, sticky='w')

# Create a frame to hold the buttons for better positioning
button_frame = tk.Frame(frame_connection)
button_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky='w')

connect_button = tk.Button(button_frame, text="Connect", command=connect_device, bg='lightgreen')
connect_button.pack(side='left', padx=5)

disconnect_button = tk.Button(button_frame, text="Disconnect", command=disconnect_device, bg='lightcoral')
disconnect_button.pack(side='left')

separator_label = tk.Label(button_frame, text=" | ")
separator_label.pack(side='left', padx=2)  # Reduced padding

save_button = tk.Button(button_frame, text="Save", command=save_input, bg='lightblue')
save_button.pack(side='left', padx=2)  # Reduced padding

load_button = tk.Button(button_frame, text="Load", command=load_saved_inputs, bg='lightyellow')
load_button.pack(side='left', padx=5)

# Frame for connection duration
connection_duration_frame = tk.Frame(root)
connection_duration_frame.place(relx=1, rely=0, anchor='ne', x=-15, y=0)

connection_duration_text_label = tk.Label(connection_duration_frame, text="Connection duration: ")
connection_duration_text_label.pack(side='left')

# Add a label to show connection duration
connection_timer_label = tk.Label(connection_duration_frame, text="00:00:00")
connection_timer_label.pack(side='left')

# Add a label to show connection status in the tab row
connection_status_label = tk.Label(root, text="●", fg="red")
connection_status_label.place(relx=1, rely=0, anchor='ne', x=-15, y=20)

# Create a connection timer instance
connection_timer = ConnectionTimer(connection_timer_label)

# VLAN tab widgets
tk.Label(frame_vlan, text="VLAN Management").grid(row=0, column=0, columnspan=2, padx=10, pady=7, sticky='w')

tk.Label(frame_vlan, text="VLAN Name:").grid(row=1, column=0, padx=10, pady=4, sticky='w')
vlan_name_entry = tk.Entry(frame_vlan)
vlan_name_entry.grid(row=1, column=1, padx=10, pady=4, sticky='w')

tk.Label(frame_vlan, text="VLAN Number:").grid(row=1, column=2, padx=10, pady=4, sticky='w')
vlan_number_entry = tk.Entry(frame_vlan)
vlan_number_entry.grid(row=1, column=3, padx=10, pady=4, sticky='w')

create_vlan_button = tk.Button(frame_vlan, text="Create VLAN", command=create_vlan, bg='lightgreen')
create_vlan_button.grid(row=1, column=4, padx=10, pady=4, sticky='w')

tk.Label(frame_vlan, text="Interfaces:").grid(row=2, column=0, padx=10, pady=4, sticky='w')
interface_combobox = ttk.Combobox(frame_vlan)
interface_combobox.grid(row=2, column=1, padx=10, pady=4, sticky='w')

tk.Label(frame_vlan, text="Mode:").grid(row=2, column=2, padx=10, pady=4, sticky='w')
mode_combobox = ttk.Combobox(frame_vlan, values=["access", "trunk"])
mode_combobox.grid(row=2, column=3, padx=10, pady=4, sticky='w')

tk.Label(frame_vlan, text="Select VLAN:").grid(row=2, column=4, padx=10, pady=4, sticky='w')
vlan_combobox = ttk.Combobox(frame_vlan)
vlan_combobox.grid(row=2, column=5, padx=10, pady=4, sticky='w')

assign_vlan_button = tk.Button(frame_vlan, text="Assign", command=assign_vlan, bg='lightblue')
assign_vlan_button.grid(row=2, column=6, padx=10, pady=4, sticky='w')

# Add new widgets for assigning native VLAN
tk.Label(frame_vlan, text="Interfaces:").grid(row=3, column=0, padx=10, pady=4, sticky='w')
native_interface_combobox = ttk.Combobox(frame_vlan)
native_interface_combobox.grid(row=3, column=1, padx=10, pady=4, sticky='w')

tk.Label(frame_vlan, text="Native VLAN:").grid(row=3, column=2, padx=10, pady=4, sticky='w')
native_vlan_entry = tk.Entry(frame_vlan)
native_vlan_entry.grid(row=3, column=3, padx=10, pady=4, sticky='w')

assign_native_vlan_button = tk.Button(frame_vlan, text="Assign Native VLAN", command=assign_native_vlan, bg='lightyellow')
assign_native_vlan_button.grid(row=3, column=4, padx=10, pady=4, sticky='w')

# Add widgets for VLAN details and interface status
tk.Label(frame_vlan, text="VLAN Details:").grid(row=4, column=0, padx=10, pady=4, sticky='w')
vlan_details_combobox = ttk.Combobox(frame_vlan, values=["show vlan brief", "show interfaces trunk", "show interfaces switchport", "show interfaces status"])
vlan_details_combobox.grid(row=4, column=1, padx=10, pady=4, sticky='w')

tk.Label(frame_vlan, text="Interfaces:").grid(row=4, column=2, padx=10, pady=4, sticky='w')
status_interface_combobox = ttk.Combobox(frame_vlan)
status_interface_combobox.grid(row=4, column=3, padx=10, pady=4, sticky='w')

show_status_button = tk.Button(frame_vlan, text="Show Status", command=show_interface_status, bg='lightcoral')
show_status_button.grid(row=4, column=4, padx=10, pady=4, sticky='w')

# Add Monitor Traffic button
monitor_traffic_button = tk.Button(frame_vlan, text="Monitor Traffic", command=monitor_traffic, bg='lightgrey')
monitor_traffic_button.grid(row=5, column=0, columnspan=5, padx=10, pady=4, sticky='w')

# Port Management tab widgets
tk.Label(frame_port, text="Port Status (double click to turn on and off)").pack(pady=10, anchor='w')
port_symbols_frame = tk.Frame(frame_port)
port_symbols_frame.pack(pady=0, anchor='w')

tk.Label(frame_port, text="Port Security").pack(pady=10, anchor='w')

port_security_frame = tk.Frame(frame_port)
port_security_frame.pack(fill='x', padx=10, pady=5, anchor='w')

tk.Label(port_security_frame, text="Interface:").pack(side='left', padx=5)
global port_security_interface_combobox
port_security_interface_combobox = ttk.Combobox(port_security_frame)
port_security_interface_combobox.pack(side='left', padx=5)

tk.Label(port_security_frame, text="Type:").pack(side='left', padx=5)
port_security_type_combobox = ttk.Combobox(port_security_frame, values=["maximum", "violation", "mac address", "aging time", "aging type"])
port_security_type_combobox.pack(side='left', padx=5)
port_security_type_combobox.bind("<<ComboboxSelected>>", on_port_security_type_change)

input_label = tk.Label(port_security_frame, text="Input:")
input_entry = tk.Entry(port_security_frame)
input_combobox = ttk.Combobox(port_security_frame)
note_label = tk.Label(port_security_frame, text="", font=("Arial", 8))

# Add the "Change" button on the same row as the input fields
change_button = tk.Button(port_security_frame, text="Change", command=apply_port_security, bg='lightgreen')
change_button.pack(side='left', padx=5)

# Add a label to show status at the bottom of the window
status_label = tk.Label(root, text="Not connected")
status_label.pack(side='bottom', fill='x', anchor='w')

# Add widgets for setting port speed and duplex
tk.Label(frame_port, text="Set port speed and duplex settings").pack(pady=10, anchor='w')

port_speed_frame = tk.Frame(frame_port)
port_speed_frame.pack(fill='x', padx=10, pady=5, anchor='w')

tk.Label(port_speed_frame, text="Interface:").pack(side='left', padx=5)
port_speed_interface_combobox = ttk.Combobox(port_speed_frame)
port_speed_interface_combobox.pack(side='left', padx=5)

tk.Label(port_speed_frame, text="Set Speed:").pack(side='left', padx=5)
port_speed_combobox = ttk.Combobox(port_speed_frame, values=["10", "100", "1000", "auto"])
port_speed_combobox.pack(side='left', padx=5)

tk.Label(port_speed_frame, text="Duplex Mode:").pack(side='left', padx=5)
port_duplex_combobox = ttk.Combobox(port_speed_frame, values=["auto", "full", "half"])
port_duplex_combobox.pack(side='left', padx=5)

set_speed_button = tk.Button(port_speed_frame, text="Set", command=set_port_speed_duplex, bg='lightblue')
set_speed_button.pack(side='left', padx=5)

# Start the Tkinter main loop
root.mainloop()
