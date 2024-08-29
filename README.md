# fridayBOT
🚀 FridayBot - The ultimate macOS automation bot! Seamlessly manage terminal scripts, Bluetooth, volume, airplane mode, time zones, and Git operations. Securely controlled by authorized users only, it’s your go-to tool for boosting productivity and automating tasks with precision.

Certainly! Below is a well-formatted, eye-catching version of the documentation suitable for a GitHub README.

---

# Telegram Bot for macOS System Automation

## Overview

This Python script automates various system tasks on a macOS machine using a Telegram bot. The bot allows you to:

- Start/stop scripts
- Manage Bluetooth connections
- Control system volume
- Toggle airplane mode
- Switch between timezones
- Kill all running applications
- Push code to specified Git repositories

**User authentication** ensures that only authorized users can interact with the bot.

---

## Prerequisites

Before setting up the script, make sure you have the following installed on your macOS:

### 1. Python 3

macOS typically comes with Python pre-installed. Check the version:

```bash
python3 --version
```

If Python is not installed, you can install it using [Homebrew](https://brew.sh/):

```bash
brew install python
```

### 2. Telegram Bot API Library

Install the `python-telegram-bot` library to enable bot interaction:

```bash
pip3 install python-telegram-bot
```

### 3. `blueutil` for Bluetooth Management

Install `blueutil` to control Bluetooth from the command line:

```bash
brew install blueutil
```

### 4. macOS Permissions

Ensure that Terminal has **Full Disk Access** and **Automation** permissions:

- Go to **System Preferences** > **Security & Privacy** > **Privacy**.
- Add **Terminal** under **Full Disk Access** and **Automation**.

---

## Create a Telegram Bot

### 1. Create a Telegram Bot

1. Open Telegram and search for **BotFather**.
2. Use the `/newbot` command to create a new bot.
3. Follow the instructions to name your bot and receive the API token.
4. Replace the placeholder `TELEGRAM_BOT_TOKEN` in the script with your bot's token.

---

## Script Configuration

### 1. Allowed Usernames

Update the `ALLOWED_USERNAMES` list with the usernames allowed to interact with the bot:

```python
ALLOWED_USERNAMES = ['MacCobra_Air_Bot', 'harshitshukla_20']  # Add more usernames as needed
```

### 2. Repository Configuration

Configure the repositories in the `REPOSITORIES` dictionary. Add paths to your repositories and specify the branch to push:

```python
REPOSITORIES = {
    'frontend': {
        'path': '/path/to/frontend/repo',
        'branch': 'dev',
    },
    'backend': {
        'path': '/path/to/backend/repo',
        'branch': 'develop',
    },
}
```

### 3. Script Mapping

Map your scripts in the `SCRIPT_COMMANDS` dictionary. Specify the paths to the shell scripts you want to run:

```python
SCRIPT_COMMANDS = {
    'stayawake': '/path/to/stayawake.sh',
    'another': '/path/to/another_script.sh',
}
```

### 4. Bluetooth MAC Address

Update the `device_mac_address` variable with the MAC address of the Bluetooth device you want to pair/unpair.

### 5. Timezone Settings

Ensure the timezones mentioned in the script (`America/Toronto` and `Asia/Calcutta`) are correct. Adjust them if needed.

---

## Script Execution

### 1. Make the Script Executable

Make the script executable by running:

```bash
chmod +x telegram_bot.py
```

### 2. Run the Script

Start the bot by running the script in the Terminal:

```bash
python3 telegram_bot.py
```

### 3. Allow Necessary Permissions

The first time the script runs, macOS may ask for permission to control Terminal, Bluetooth, and other system features. Ensure you grant these permissions.

---

## Interact with the Bot

### 1. Start the Bot

1. Open Telegram and start a chat with your bot.
2. Use the `/start` command to see the available options and buttons.
3. You can now:
   - Start/stop scripts
   - Push code to repositories
   - Toggle Bluetooth
   - Control system volume
   - Switch timezones
   - Kill all running applications
   - Stop the bot

---

## Script Functions Overview

### Logging Configuration

- **Purpose:** Tracks events and errors, setting the logging level to `INFO`.

### User Authentication

- **Function:** `is_user_allowed(username: str) -> bool`
- **Purpose:** Verifies if the user interacting with the bot is allowed by checking against the `ALLOWED_USERNAMES` list.

### Start Function

- **Function:** `start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None`
- **Purpose:** Displays control buttons to start/stop scripts, toggle Bluetooth, toggle airplane mode, control volume, switch timezones, kill all apps, or push code to repositories.

### Bluetooth Management

- **Function:** `is_bluetooth_on() -> bool`
  - **Purpose:** Checks if Bluetooth is powered on.
- **Function:** `toggle_bluetooth_device(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None`
  - **Purpose:** Toggles Bluetooth pairing/unpairing with a specified device.

### Script Management

- **Function:** `run_script(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str) -> None`
  - **Purpose:** Starts a specified script in a new Terminal window, ensuring that only one script runs at a time.
- **Function:** `stop_script(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None`
  - **Purpose:** Stops the currently running script by closing the Terminal window.

### Volume Control

- **Function:** `toggle_volume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None`
  - **Purpose:** Toggles the system volume between muted and unmuted.

### Airplane Mode

- **Function:** `control_airplane_mode(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str) -> None`
  - **Purpose:** Turns on airplane mode by disabling Wi-Fi.

### Timezone Switching

- **Function:** `toggle_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None`
  - **Purpose:** Switches between two predefined timezones.

### Kill All Applications

- **Function:** `kill_all_apps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None`
  - **Purpose:** Kills all running applications except for Telegram and the system's UI server.

### Git Operations

- **Helper Functions:**
  - `is_rebase_in_progress()`: Checks if a Git rebase is in progress.
  - `is_head_detached()`: Checks if the HEAD is detached in the Git repository.
  - `check_network_connectivity()`: Checks if the system has network connectivity.
  - `check_unstaged_changes()`: Checks if there are unstaged changes in the Git repository.
  - `check_branch_up_to_date()`: Ensures the current branch is up-to-date with the remote.
- **Push Code:**
  - `push_code(update, context: ContextTypes.DEFAULT_TYPE, repo_key: str) -> None`: Handles pushing code to a specified repository with enhanced error handling and notifications.
  - `proceed_with_push(update, branch_name: str, repo_key: str) -> None`: Manages the process of merging the current branch into the target branch and handling conflicts during the Git operations.

### Bot Control

- **Function:** `stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None`
  - **Purpose:** Stops the bot and any running script.

### Button Callback

- **Function:** `button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None`
  - **Purpose:** Handles all button interactions, mapping the button's callback data to the appropriate function.

### Main Function

- **Function:** `main()`
  - **Purpose:** Initializes the bot, sets up command handlers, and starts polling Telegram for updates.

---

## Automate Script Startup (Optional)

### 1. Create a LaunchAgent

To run the script automatically on startup, create a LaunchAgent:

1. Create a new `.plist` file in `~/Library/LaunchAgents/` (e.g., `com.username.telegram_bot.plist`):

   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.username.telegram_bot</string>
       <key>ProgramArguments</key>
       <array>
           <string>/usr/bin/python3</string>
           <string>/Users/yourusername/path/to/telegram_bot.py</string>
       </array>
       <key>RunAtLoad</key>
       <true/>
       <key>KeepAlive</key>
       <true/>
   </dict>
   </plist>
   ```

2. Replace `yourusername` and `/path/to/telegram_bot.py` with your username and the correct script path.
3. Load the agent:

   ```bash
   launchctl load ~/Library/LaunchAgents/com.username.telegram_bot.plist
   ```

---

## Testing and Debugging

- **Test All Functions:** Ensure all functions such as starting/stopping scripts, Bluetooth toggling, volume control, and Git operations work as expected.
- **Check Logs:** Review logs in the Terminal to troubleshoot any issues.

---

## Final Notes

- This script is specifically designed for a macOS environment and leverages macOS

-specific tools like AppleScript.
- Ensure paths and repository settings are correctly configured according to your system.
- Regularly update the script if you add more repositories, scripts, or functionalities.

---

Following these steps will ensure that you set up and run the provided Python script on your Mac successfully, with a thorough understanding of each component's functionality.

---

This documentation is designed to be clear and engaging, making it suitable for a GitHub README file. The headings and code blocks provide a structured guide, making it easy for users to follow along.
