import pystray
from PIL import Image, ImageDraw
import subprocess
import threading
import os
import time

# --- CONFIG ---
CONNECT_SCRIPT = r"<path to connect script>"
STOP_SCRIPT = r"<path to stop script>"
ICON_PATH = r"<path to desired icon>"

# --- STATE ---
status_text = "Disconnected"
is_processing = False  # Functions as a lock so I don't break my network by spamming :)

def get_status_text(item):
    return f"Status: {status_text}"

def create_image():
    # Load my very cool custom icon
    if os.path.exists(ICON_PATH):
        return Image.open(ICON_PATH).resize((64, 64))

    # Make a default image in case custom doesnt work
    # AI made this, idk what it looks like
    image = Image.new('RGB', (64, 64), (30, 30, 30))
    dc = ImageDraw.Draw(image)

    # Color logic based on status
    if status_text == "Connected":
        color = "green"
    elif status_text == "Disconnected":
        color = "red"
    elif "ing" in status_text:  # Connecting... / Disconnecting...
        color = "yellow"
    else:
        color = "orange"  # Error state

    dc.ellipse((10, 10, 54, 54), fill=color)
    return image

def set_ui_state(new_status):
    global status_text
    status_text = new_status
    icon.icon = create_image()
    icon.title = f"VPN: {status_text}"
    icon.update_menu()


def execute_ps_script(script_path, processing_text, success_text, fail_text):
    global is_processing
    if is_processing:
        return

    is_processing = True
    set_ui_state(processing_text)

    try:
        result = subprocess.run(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", script_path],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        if result.returncode == 0:
            set_ui_state(success_text)
        else:
            print(f"Script failed with code {result.returncode}:\n{result.stderr}")
            set_ui_state(fail_text)

    except Exception as e:
        print(f"Python subprocess error: {e}")
        set_ui_state(fail_text)

    finally:
        is_processing = False


def on_connect(icon, item):
    if status_text != "Connected" and not is_processing:
        threading.Thread(target=execute_ps_script, args=(CONNECT_SCRIPT, "Connecting...", "Connected", "Error: Failed"),
                         daemon=True).start()

def on_disconnect(icon, item):
    if status_text != "Disconnected" and not is_processing:
        threading.Thread(target=execute_ps_script,
                         args=(STOP_SCRIPT, "Disconnecting...", "Disconnected", "Error: Failed"), daemon=True).start()


def delayed_startup(icon):
    # Change text
    set_ui_state("Waiting for Network...")

    # Wait for connection
    time.sleep(10)

    # Now connect
    on_connect(icon, None)

def on_startup(icon):
    icon.visible = True
    # Trigger connect once its set up
    threading.Thread(target=delayed_startup, args=(icon,), daemon=True).start()


# --- BUILD MENU ---
menu = pystray.Menu(
    pystray.MenuItem(get_status_text, lambda x: None, enabled=False),
    pystray.Menu.SEPARATOR,
    pystray.MenuItem("Connect", on_connect),
    pystray.MenuItem("Disconnect", on_disconnect),
    pystray.Menu.SEPARATOR,
)

# Start the Tray Icon (Passing on_startup to auto-run logic)
icon = pystray.Icon("VPN_Widget", create_image(), "VPN: Initializing...", menu)
icon.run(setup=on_startup)