# PyTelegramRichPost Deployment Manual

*Step-by-step manual for deploying on Linux server.*

## 1. Download the Release

Download the archive directly from the [GitHub Releases](https://github.com/vakarianplay/telegram_bots/releases/tag/v1.0) or download it via the terminal using `wget`:

```bash
wget https://github.com/vakarianplay/telegram_bots/releases/download/v1.0/PyTelegramRichPost.zip
```

## 2. Extract the Archive

```bash
# Install unzip
sudo apt update && sudo apt install unzip -y

# Extract the archive
unzip PyTelegramRichPost.zip
cd PyTelegramRichPost
```

## 3. Install Dependencies

Install the required YAML parsing library:

```bash
pip3 install pyyaml --break-system-packages
```

## 4. Configure the App

Edit `config.yaml` file in the directory of the project:

```bash
nano config.yaml
```

The configuration file using the following structure:

```yaml
server:
  host: "0.0.0.0"       # Network interface to bind to (0.0.0.0 listens on all interfaces)
  port: 8080            # Target port for the application web server

templates:
  index: "templates/index.html"  # Path to the main dashboard template
  help: "templates/help.html"    # Path to the documentation/help template

telegram:
  request_timeout: 20   # Telegram API request timeout limit in seconds

ui:
  title: "RichMessage Publisher" # The header title displayed on the web interface
  icon:
    source: "simpleicons"   # Icon source type: simpleicons | url | file | none
    value: "task"           # Site slug from simpleicons.org or a direct URL/file path
    # Alternative URL configuration example:
    # source: url
    # value: https://githubusercontent.com
  favicon:
    source: "url"           # Favicon source type: simpleicons | url | file | none
    value: "https://simpleicons.org"
```

## 5. Create a systemd Service

To ensure the application runs continuously in the background and restarts automatically on failures or server reboots, create a systemd service unit file:

```bash
sudo nano /etc/systemd/system/tg_rich.service
```

```ini
[Unit]
Description=PyTelegramRichPost Service
After=network.target

[Service]
Type=simple
User=user
WorkingDirectory=/path/to/PyTelegramRichPost
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 6. Start and Enable the Service

Reload the systemd manager configuration, enable the service to launch at boot, and start the application:

```bash
# Reload systemd manager configuration
sudo systemctl daemon-reload

# Enable service auto-start on boot
sudo systemctl enable tg_rich.service

# Start the service immediately
sudo systemctl start tg_rich.service

# Verify service running status
sudo systemctl status tg_rich.service
```
