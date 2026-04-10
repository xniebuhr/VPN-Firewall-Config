# Overview
This project is a custom, fully routed VPN designed to bypass DPI and strict firewalls. Standard WireGuard traffic is easily identifiable and frequently blocked by restrictive networks. To solve this, I designed a system that encapsulates WireGuard UDP traffic within an Xray REALITY (VLESS/TCP) tunnel. To an outside observer or ISP, the VPN traffic appears as standard, secure HTTPS communicating with a legitimate web server.

## High-Level Architecture
The system is split into a Windows client and an Ubuntu-based EC2 server, interacting through a proxy tunnel.

Client-side traffic flow:
1. System Interface: Windows routes all internet traffic through the virtual WireGuard network adapter
2. Local inbound: WireGuard points to a local endpoint (127.0.0.1:51820)
3. Encapsulation: A local Xray-core instance uses a `dokodemo-door` inbound to capture the WireGuard UDP packets
4. Obfuscation: Xray wraps the UDP packets in a VLESS TCP tunnel, secures it with the REALITY protocol, and sends it to my VM over port 443

Server-side traffic flow:
1. Decapsulation: The remote Xray-core instance receives the disguised traffic on port 443 and unwraps the VLESS layer
2. Local Delivery: Xray's freedom outbound delivers the raw WireGuard UDP packets to the local WireGuard server listening on port 51820
3. NAT & Egress: WireGuard decrypts the payload, and iptables routes the traffic out to the open internet

## Tech Stack
- Infrastructure: AWS EC2 t3.micro (Ubuntu), Ansible 
- Networking Protocols: WireGuard, Xray-core (VLESS/REALITY/XTLS)
- Client UI & Automation: Python, PowerShell, Windows Task Scheduler
- Security: UFW, Fail2ban, public-key crypto

## Repo Structure & Dev Notes
Because of the many moving parts in the setup located in different places, I structured this a bit differently to organize things and make it easy to read. Additionally, all keys, IDs, filepaths, and domains have been redacted for security purposes.

- `VPN-client`
    - Contains the relevant configuration files used by the client, which is my laptop.
    - `widget` houses the python script and relevant powershell scripts. The flow of this is a little weird because of the nature of running the scripts with admin. So the task scheduler runs the launch-widget script on login, giving it admin privileges. Then the widget script creates a small icon which when clicked on gives the option for connect and disconnect, which call the respective powershell scripts to automatically handle all routing and processes with great error handling. This is the only to run it sesamlessly in Windows, but if it ain't broke don't fix it I suppose. It also has a custom icon, which is a warning symbol because I think it's funny.
- `VPN-server`
    - Contains the server-side configuration for Xray and WireGuard.
- `firewall`
    - Contains the ansible setup, managed by the tasks. The firewall file simply imports the tasks and holds a handler. The inventory file simply points ansible to my VM. You might notice that `inventory.ini` connects to 10.0.0.1, but if you look at the config files you can figure out that this only works when my VPN is connected, so 10.0.0.1 simply points it at the server so I don't try to connect to the server from inside the server and hairpin.
    - `tasks` just holds the relevant firewall rules, organized into sections.
