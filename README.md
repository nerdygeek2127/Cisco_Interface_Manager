# CiscoNetworkManager

A Python-based GUI application for managing Cisco network devices, enabling VLAN creation, port configuration, traffic monitoring, and connection management using Tkinter and Netmiko.

## Features

- **Connect and Disconnect**: Connect to and disconnect from Cisco devices.
- **Save and Load Configurations**: Save connection configurations for reuse and load them as needed.
- **VLAN Management**: Create VLANs, assign VLANs to interfaces, and assign native VLANs.
- **Port Management**: Monitor port status, configure port security, and set port speed and duplex settings.
- **Traffic Monitoring**: Monitor traffic on the device interfaces.

## Prerequisites

- Python 3.x
- Netmiko library
- Tkinter library (comes pre-installed with Python)

## Installation

1. **Clone the repository**:
    ```sh
    git clone https://github.com/nerdygeek2127/Cisco_Interface_Manager.git
    cd Cisco_Interface_Manager
    ```

2. **Install the required Python packages**:
    ```sh
    pip install netmiko
    ```

## Usage

1. **Run the application**:
    ```sh
    python cisco_command_executor.py
    ```

2. **Use the GUI to**:
    - Enter the device connection details (host, username, password, and secret).
    - Click "Connect" to establish a connection to the device.
    - Use the VLAN tab to create VLANs, assign VLANs to interfaces, and assign native VLANs.
    - Use the Port Management tab to monitor port status, configure port security, and set port speed and duplex settings.
    - Click "Disconnect" to disconnect from the device.

## File Structure

- `cisco_command_executor.py`: The main application file containing the Tkinter GUI and the functionality for managing Cisco devices.
- `running_config.json`: A JSON file used to save the running configuration commands.
- `saved_inputs.json`: A JSON file used to save and load connection configurations.

## Code Overview

### Main Components

- **Connection Management**:
  - `connect_device()`: Connects to the Cisco device using the provided connection details.
  - `disconnect_device()`: Disconnects from the Cisco device.
  - `save_input()`: Saves the connection details to `saved_inputs.json`.
  - `load_saved_inputs()`: Loads the saved connection details from `saved_inputs.json`.

- **VLAN Management**:
  - `create_vlan()`: Creates a VLAN on the connected device.
  - `assign_vlan()`: Assigns a VLAN to a specified interface in either access or trunk mode.
  - `assign_native_vlan()`: Assigns a native VLAN to a specified interface.
  - `show_interface_status()`: Shows the status of a specified interface.

- **Port Management**:
  - `apply_port_security()`: Applies port security settings to a specified interface.
  - `set_port_speed_duplex()`: Sets the speed and duplex mode for a specified interface.
  - `populate_interfaces_and_vlans()`: Populates the interface and VLAN comboboxes with data from the connected device.
  - `populate_port_status()`: Populates the port status indicators with the status of the interfaces.

- **Traffic Monitoring**:
  - `monitor_traffic()`: Monitors traffic on the device interfaces and displays the output.

### Helper Classes

- **ConnectionTimer**: A helper class to track and display the duration of the connection.

### GUI Structure

The application uses a Tkinter Notebook widget to organize the GUI into three main tabs:
- **Connection Tab**: For entering connection details, connecting to the device, and saving/loading configurations.
- **VLAN Tab**: For creating VLANs, assigning VLANs to interfaces, and viewing VLAN/interface details.
- **Port Management Tab**: For monitoring port status, configuring port security, and setting port speed and duplex settings.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Feel free to submit issues, fork the repository, and send pull requests. Contributions are welcome!

## Contact

For any inquiries, please contact nerdygeek2127@example.com.
