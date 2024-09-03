import subprocess
import logging
import os
import signal
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest, RetryAfter, NetworkError
import asyncio
import threading
import PIL
from PIL import Image
import os

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Suppress httpx info logs
logging.getLogger("httpx").setLevel(logging.WARNING)

# Replace with your Telegram bot token
TELEGRAM_BOT_TOKEN = 'Your Telegram Bot Token'

# List of allowed usernames
ALLOWED_USERNAMES = ['yourTelegramBotUsername', 'yourTelegramUsername']  # Add more usernames as needed

# Repository configurations (Add more repositories as needed)
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
    # Add more repositories here
}

# Command to script mapping for easy scalability
SCRIPT_COMMANDS = {
    'stayawake': '/path/to/stayawake.sh',
    'another': '/path/to/another_script.sh',
}

# Track the currently running script
current_running_script = None
bluetooth_paired = False  # Track the Bluetooth pairing state
volume_muted = False  # Track the volume state
current_timezone = 'America/Toronto'  # Track the current timezone

# Function to verify if the user is allowed
def is_user_allowed(username: str) -> bool:
    if username not in ALLOWED_USERNAMES:
        logging.warning(f"Unauthorized access attempt by {username}")
        return False
    return True

# Define a function to start the bot and show the control buttons
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.message.from_user.username
    if not is_user_allowed(username):
        await update.message.reply_text('You are not authorized to use this bot.')
        return

    global bluetooth_paired, volume_muted, current_timezone
    logging.info("Received /start command")

    buttons = [
        [InlineKeyboardButton(f'🚀 Start Air {cmd.capitalize()}', callback_data=f'start_{cmd}') for cmd in SCRIPT_COMMANDS.keys()],
        [InlineKeyboardButton('📸 Take Snap', callback_data='snap')],
        [InlineKeyboardButton('🔄 Unpair Bluetooth' if bluetooth_paired else '🔗 Pair Bluetooth', callback_data='toggle_bluetooth')],
        [InlineKeyboardButton('✈️ Turn On Airplane Mode', callback_data='turn_on_airplane_mode')],
        [InlineKeyboardButton('🔊 Volume Off' if not volume_muted else '🔈 Volume On', callback_data='toggle_volume')],
        [InlineKeyboardButton(f'🌍 Switch to {"Asia/Calcutta" if current_timezone == "America/Toronto" else "America/Toronto"}', callback_data='toggle_timezone')],
        [InlineKeyboardButton('💥 Kill All Apps', callback_data='kill_all_apps')],
        [InlineKeyboardButton(f'💾 Push {repo.capitalize()}', callback_data=f'push_code_{repo}') for repo in REPOSITORIES.keys()],
    ]

    # Show the stop button only if a script is currently running
    if current_running_script:
        buttons.append([InlineKeyboardButton('🛑 Stop Current Script Air', callback_data='stop')])

    # Add a button to stop the bot
    buttons.append([InlineKeyboardButton('⛔ Stop Bot Air', callback_data='stop_bot')])

    reply_markup = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(
        'Use the buttons below to push code, start or stop scripts, pair/unpair Bluetooth, turn on airplane mode, toggle volume, switch timezone, kill all apps, or stop the bot.',
        reply_markup=reply_markup
    )

# Function to check Bluetooth power status
def is_bluetooth_on() -> bool:
    try:
        output = subprocess.check_output(['env', 'BLUEUTIL_ALLOW_ROOT=1', 'blueutil', '--power']).decode().strip()
        return output == '1'
    except subprocess.CalledProcessError as e:
        logging.error(f"Error checking Bluetooth power status: {e}")
        return False

# Function to run a script in the background with Terminal management
async def run_script(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str) -> None:
    username = update.callback_query.from_user.username
    if not is_user_allowed(username):
        await update.callback_query.message.reply_text('You are not authorized to use this bot.')
        return

    global current_running_script
    script_path = SCRIPT_COMMANDS.get(command)

    # Stop any currently running script before starting a new one
    if current_running_script:
        await stop_script(update, context)

    if not script_path:
        await update.callback_query.message.reply_text(f'No script found for command: /{command}')
        return

    try:
        logging.info(f"Running script for /{command}")

        # AppleScript to hide all applications and open Terminal with focus on the current desktop
        applescript_command = f'''
        tell application "System Events"
            set visible of every process to false -- Hide all applications
            delay 1
        end tell
        tell application "Terminal"
            do script "{script_path}" -- Run the script in a new Terminal window
            activate -- Bring Terminal to the front
        end tell
        tell application "System Events"
            tell process "Terminal"
                set frontmost to true -- Ensure Terminal is frontmost
            end tell
        end tell
        '''

        subprocess.run(['osascript', '-e', applescript_command], check=True)

        current_running_script = command
        await update.callback_query.message.reply_text(f'{command.capitalize()} script is now running in a new Terminal window...')

        # Refresh the buttons to show the stop option
        await start(update.callback_query, context)

    except Exception as e:
        logging.error(f"Error while running script for /{command}: {e}")
        await update.callback_query.message.reply_text(f'Failed to run {command} script.')

# Function to toggle Bluetooth pairing/unpairing
async def toggle_bluetooth_device(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.callback_query.from_user.username
    if not is_user_allowed(username):
        await update.callback_query.message.reply_text('You are not authorized to use this bot.')
        return

    global bluetooth_paired
    try:
        if not bluetooth_paired:
            # Ensure Bluetooth is turned on and pair with the device
            subprocess.run(['env', 'BLUEUTIL_ALLOW_ROOT=1', 'blueutil', '--power', 'on'], check=True)
            await update.callback_query.message.reply_text('Bluetooth is turned on.')

            # Pair with a specific Bluetooth device
            device_mac_address = "XX:XX:XX:XX:XX:XX"  # Replace with your Bluetooth device's MAC address
            subprocess.run(['env', 'BLUEUTIL_ALLOW_ROOT=1', 'blueutil', '--connect', device_mac_address], check=True)
            await update.callback_query.message.reply_text(f'Attempting to pair with device {device_mac_address}...')
            bluetooth_paired = True
        else:
            # Check if Bluetooth is already off
            if not is_bluetooth_on():
                bluetooth_paired = False
                await update.callback_query.message.reply_text('Bluetooth is already off, nothing to unpair.')
            else:
                # Unpair the specific Bluetooth device
                device_mac_address = "E8:EE:CC:C5:0A:40"  # Replace with your device's MAC address
                subprocess.run(['env', 'BLUEUTIL_ALLOW_ROOT=1', 'blueutil', '--disconnect', device_mac_address], check=True)
                # subprocess.run(['env', 'BLUEUTIL_ALLOW_ROOT=1', 'blueutil', '--power', 'off'], check=True)
                await update.callback_query.message.reply_text(f'Device {device_mac_address} disconnected successfully.')
                bluetooth_paired = False

        # Refresh the buttons to reflect the new state
        await start(update.callback_query, context)

    except Exception as e:
        logging.error(f"Error while toggling Bluetooth device: {e}")
        await update.callback_query.message.reply_text('Failed to toggle Bluetooth device.')

# Function to toggle volume on/off
async def toggle_volume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.callback_query.from_user.username
    if not is_user_allowed(username):
        await update.callback_query.message.reply_text('You are not authorized to use this bot.')
        return

    global volume_muted
    try:
        if volume_muted:
            subprocess.run(['osascript', '-e', 'set volume output volume 50'], check=True)
            await update.callback_query.message.reply_text('Volume turned on.')
            volume_muted = False
        else:
            subprocess.run(['osascript', '-e', 'set volume output volume 0'], check=True)
            await update.callback_query.message.reply_text('Volume turned off.')
            volume_muted = True

        # Refresh the buttons to reflect the new state
        await start(update.callback_query, context)

    except Exception as e:
        logging.error(f"Error while toggling volume: {e}")
        await update.callback_query.message.reply_text('Failed to toggle volume.')

# Function to control Airplane mode using networksetup
async def control_airplane_mode(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str) -> None:
    username = update.callback_query.from_user.username
    if not is_user_allowed(username):
        await update.callback_query.message.reply_text('You are not authorized to use this bot.')
        return

    try:
        if mode == 'on':
            subprocess.run(['networksetup', '-setairportpower', 'en0', 'off'], check=True)
            await update.callback_query.message.reply_text('Airplane mode turned on.')

    except Exception as e:
        logging.error(f"Error while toggling Airplane mode: {e}")
        await update.callback_query.message.reply_text('Failed to turn on Airplane mode.')

# Function to toggle between timezones
async def toggle_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.callback_query.from_user.username
    if not is_user_allowed(username):
        await update.callback_query.message.reply_text('You are not authorized to use this bot.')
        return

    global current_timezone
    try:
        # Use the correct timezone identifiers
        new_timezone = 'Asia/Calcutta' if current_timezone == 'America/Toronto' else 'America/Toronto'
        subprocess.run(['sudo', 'systemsetup', '-settimezone', new_timezone], check=True)
        current_timezone = new_timezone
        await update.callback_query.message.reply_text(f'Timezone switched to {current_timezone}.')

        # Refresh the buttons to reflect the new state
        await start(update.callback_query, context)

    except Exception as e:
        logging.error(f"Error while toggling timezone: {e}")
        await update.callback_query.message.reply_text(f'Failed to toggle timezone.')

# Function to kill all running applications except the bot script
async def kill_all_apps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.callback_query.from_user.username
    if not is_user_allowed(username):
        await update.callback_query.message.reply_text('You are not authorized to use this bot.')
        return

    try:
        # Get the list of all running applications
        apps = subprocess.check_output(['osascript', '-e', 'tell application "System Events" to get the name of every application process whose background only is false']).decode().strip().split(', ')

        for app in apps:
            if app not in ['Telegram', 'SystemUIServer']:  # Don't kill SystemUIServer or the bot itself
                subprocess.run(['osascript', '-e', f'tell application "{app}" to quit'], check=True)

        # Explicitly quit VS Code and Microsoft Teams
        subprocess.run(['osascript', '-e', 'tell application "Visual Studio Code" to quit'], check=True)
        subprocess.run(['osascript', '-e', 'tell application "Microsoft Teams" to quit'], check=True)

        await update.callback_query.message.reply_text('All running applications have been killed.')

    except Exception as e:
        logging.error(f"Error while killing all applications: {e}")
        await update.callback_query.message.reply_text('Failed to kill all applications.')

# Function to stop the currently running script and close the Terminal window using AppleScript
async def stop_script(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.callback_query.from_user.username
    if not is_user_allowed(username):
        await update.callback_query.message.reply_text('You are not authorized to use this bot.')
        return

    global current_running_script

    if not current_running_script:
        await update.callback_query.message.reply_text('No running script found.')
        return

    try:
        logging.info(f"Stopping the script /{current_running_script}")
        
        # Close the Terminal window via AppleScript
        close_command = """
        tell application "System Events"
            tell process "Terminal"
                keystroke "w" using command down
                delay 0.5
                keystroke tab
                delay 0.5
                keystroke return
            end tell
        end tell
        """
        subprocess.run(['osascript', '-e', close_command], check=True)
        
        current_running_script = None
        await update.callback_query.message.reply_text('Script has been stopped.')

    except Exception as e:
        logging.error(f"Error while stopping script: {e}")
        await update.callback_query.message.reply_text('Failed to stop the script.')

    # Refresh the buttons
    await start(update.callback_query, context)

# Function to stop the bot itself
async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.callback_query.from_user.username
    if not is_user_allowed(username):
        await update.callback_query.message.reply_text('You are not authorized to use this bot.')
        return

    logging.info("Received request to stop the bot")
    await update.callback_query.message.reply_text('Stopping the bot...')

    # Stop the script if one is running
    if current_running_script:
        await stop_script(update, context)

    os.kill(os.getpid(), signal.SIGTERM)

# Function to check if a rebase is in progress
def is_rebase_in_progress():
    rebase_merge_path = os.path.join('.git', 'rebase-merge')
    return os.path.exists(rebase_merge_path)

# Function to check if HEAD is detached
def is_head_detached():
    head_file_path = os.path.join('.git', 'HEAD')
    with open(head_file_path, 'r') as head_file:
        return 'refs/heads' not in head_file.read()

# Function to check network connectivity
def check_network_connectivity():
    try:
        subprocess.check_output(['ping', '-c', '1', 'github.com'], stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError:
        return False

# Function to check for unstaged changes including untracked files
def check_unstaged_changes():
    # Include both staged, modified, and untracked files in the check
    result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
    return result.stdout.strip() != ''

# Function to ensure the branch is up-to-date
def check_branch_up_to_date():
    subprocess.run(['git', 'fetch'], check=True)
    status = subprocess.check_output(['git', 'status', '-uno'], universal_newlines=True)
    return 'Your branch is up to date' in status

# Retry logic for transient errors
def retry_operation(operation, retries=3):
    for attempt in range(retries):
        try:
            operation()
            return
        except subprocess.CalledProcessError as e:
            logging.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt == retries - 1:
                raise

# Function to push code with enhanced error handling, optimizations, and bot notifications
async def push_code(update, context: ContextTypes.DEFAULT_TYPE, repo_key: str) -> None:
    username = update.callback_query.from_user.username
    if not is_user_allowed(username):
        await update.callback_query.message.reply_text('You are not authorized to use this bot.')
        return

    repo_config = REPOSITORIES.get(repo_key)
    if not repo_config:
        await update.callback_query.message.reply_text(f"Invalid repository key: {repo_key}")
        return

    repo_path = repo_config['path']
    target_branch = repo_config['branch']
    branch_name = None

    try:
        logging.info(f"Starting enhanced code push process for {repo_key}")
        await update.callback_query.message.reply_text(f"Starting enhanced code push process for {repo_key}...")

        os.chdir(repo_path)

        # Check if HEAD is detached
        if is_head_detached():
            await update.callback_query.message.reply_text(f"Error: You are in a detached HEAD state in {repo_key}. Please check out a branch before proceeding.")
            logging.error("Detached HEAD detected.")
            return

        # Check network connectivity
        if not check_network_connectivity():
            await update.callback_query.message.reply_text(f"No network connectivity for {repo_key}. Please check your connection and try again.")
            return

        await update.callback_query.message.reply_text(f"Network connectivity check passed for {repo_key}.")

        # Check for unstaged changes
        if check_unstaged_changes():
            await update.callback_query.message.reply_text(f"Unstaged changes detected in {repo_key}. Staging changes now...")
            subprocess.run(['git', 'add', '.'], check=True)
            await update.callback_query.message.reply_text(f"All changes staged successfully in {repo_key}.")
        
        await update.callback_query.message.reply_text(f"No unstaged changes detected in {repo_key}.")

        # Check if there is anything to commit
        commit_status = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        if commit_status.stdout.strip() == "":
            await update.callback_query.message.reply_text(f"No changes to commit in {repo_key}. Checking if '{target_branch}' branch has updates.")
            logging.info(f"No changes to commit in {repo_key}. Checking if '{target_branch}' branch has updates.")

            # Fetch the latest changes from target branch
            subprocess.run(['git', 'fetch'], check=True)
            # Check if target branch has new commits
            dev_status = subprocess.run(['git', 'rev-list', f'HEAD...origin/{target_branch}', '--count'], capture_output=True, text=True)
            if dev_status.stdout.strip() != "0":
                await update.callback_query.message.reply_text(f"The '{target_branch}' branch has updates in {repo_key}. Attempting to pull and merge.")
                logging.info(f"The '{target_branch}' branch has updates in {repo_key}. Attempting to pull and merge.")

                # Pull and rebase target branch into current branch here
                subprocess.run(['git', 'pull', '--rebase', 'origin', target_branch], check=True)
                await update.callback_query.message.reply_text(f"Successfully rebased '{target_branch}' into your branch in {repo_key}.")

                # Push the updated branch to the remote
                push_result = subprocess.run(['git', 'push'], capture_output=True, text=True)
                if 'non-fast-forward' in push_result.stderr:
                    await update.callback_query.message.reply_text(f"Push rejected due to remote changes in {repo_key}. Attempting to pull, rebase, and push again...")
                    # Fetch and rebase with the latest remote changes
                    subprocess.run(['git', 'pull', '--rebase'], check=True)
                    # Attempt to push again
                    subprocess.run(['git', 'push'], check=True)
                    await update.callback_query.message.reply_text(f"Push after pull and rebase completed successfully in {repo_key}.")
                elif push_result.returncode != 0:
                    raise subprocess.CalledProcessError(push_result.returncode, 'git push')

            # Proceed to the push process
            branch_name = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], universal_newlines=True).strip()
            await proceed_with_push(update, branch_name, repo_key)
            return

        # Proceed with commit if there are changes
        subprocess.run(['git', 'commit', '-m', 'added latest changes'], check=True)
        await update.callback_query.message.reply_text(f"Committed changes in {repo_key}.")

        # Step 3: Get current timestamp in the latest commit
        timestamp = subprocess.check_output(['git', 'log', '-1', '--format=%cd'], universal_newlines=True).strip()
        logging.info(f"Latest commit timestamp for {repo_key}: {timestamp}")
        await update.callback_query.message.reply_text(f"Latest commit timestamp for {repo_key}: {timestamp}")

        # Step 4: Ensure the branch is up-to-date
        if not check_branch_up_to_date():
            await update.callback_query.message.reply_text(f"Your branch in {repo_key} is not up-to-date. Fetching the latest changes...")
            subprocess.run(['git', 'pull', '--rebase'], check=True)
            await update.callback_query.message.reply_text(f"Branch in {repo_key} is now up-to-date.")

        # Step 5: Attempt to push with retry logic
        try:
            await update.callback_query.message.reply_text(f"Attempting to push changes to the remote repository for {repo_key}...")
            push_result = subprocess.run(['git', 'push'], capture_output=True, text=True)
            if 'non-fast-forward' in push_result.stderr:
                await update.callback_query.message.reply_text(f"Push rejected due to remote changes in {repo_key}. Attempting to pull, rebase, and push again...")
                # Pull and rebase with the latest remote changes
                subprocess.run(['git', 'pull', '--rebase'], check=True)
                # Attempt to push again
                subprocess.run(['git', 'push'], check=True)
                await update.callback_query.message.reply_text(f"Push after pull and rebase completed successfully in {repo_key}.")
            elif push_result.returncode != 0:
                raise subprocess.CalledProcessError(push_result.returncode, 'git push')
            else:
                await update.callback_query.message.reply_text(f"Pushed changes to the remote repository for {repo_key}.")
        except subprocess.CalledProcessError as e:
            raise e  # Re-raise if it's a different error

        # Step 6: Get current branch name
        branch_name = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], universal_newlines=True).strip()
        await update.callback_query.message.reply_text(f"Current branch in {repo_key}: {branch_name}")

        # Proceed with the push process if there were no issues in the above steps
        await proceed_with_push(update, branch_name, repo_key)

    except subprocess.CalledProcessError as e:
        logging.error(f"Error during Git operations in {repo_key}: {e}")
        await update.callback_query.message.reply_text(f"Failed during Git operation in {repo_key}: {e}")

# Function to handle the process from step #6 onwards
async def proceed_with_push(update, branch_name: str, repo_key: str) -> None:
    username = update.callback_query.from_user.username
    if not is_user_allowed(username):
        await update.callback_query.message.reply_text('You are not authorized to use this bot.')
        return

    repo_config = REPOSITORIES.get(repo_key)
    if not repo_config:
        await update.callback_query.message.reply_text(f"Invalid repository key: {repo_key}")
        return

    target_branch = repo_config['branch']

    try:
        # Step 7: Attempt to merge to target_branch
        await update.callback_query.message.reply_text(f"Attempting to merge {branch_name} into '{target_branch}' branch in {repo_key}...")
        subprocess.run(['git', 'checkout', target_branch], check=True)
        merge_result = subprocess.run(
            ['git', 'merge', branch_name],
            capture_output=True,
            text=True,
            env={**os.environ, "GIT_EDITOR": "true"}  # Skipping the interactive editor
        )

        if 'CONFLICT' in merge_result.stdout or 'CONFLICT' in merge_result.stderr:
            await update.callback_query.message.reply_text(f"Conflicts detected in branch {branch_name} while merging into '{target_branch}' in {repo_key}. Code push process stopped.")
            logging.error(f"Conflicts detected in branch {branch_name} while merging into '{target_branch}' in {repo_key}")
            return

        await update.callback_query.message.reply_text(f"Merged {branch_name} into '{target_branch}' branch successfully in {repo_key}.")

        # Step 9: Pull the latest changes from target_branch and check for conflicts
        await update.callback_query.message.reply_text(f"Pulling the latest changes from '{target_branch}' branch in {repo_key}...")
        pull_result = subprocess.run(
            ['git', 'pull', '--rebase'],
            capture_output=True,
            text=True,
            env={**os.environ, "GIT_EDITOR": "true"}  # Skipping the interactive editor
        )

        if 'CONFLICT' in pull_result.stdout or 'CONFLICT' in pull_result.stderr:
            await update.callback_query.message.reply_text(f"Conflicts detected while pulling from '{target_branch}' in {repo_key}. Code push process stopped. Please resolve the conflicts manually and continue the rebase process.")
            logging.error(f"Conflicts detected while pulling from '{target_branch}' in {repo_key}")
            return

        await update.callback_query.message.reply_text(f"Pulled the latest changes from '{target_branch}' branch successfully in {repo_key}.")

        # Proceed with the push process
        subprocess.run(['git', 'push'], check=True)
        await update.callback_query.message.reply_text(f"Pushed changes to '{target_branch}' branch in {repo_key}.")

        # Step 12: Notify success
        await update.callback_query.message.reply_text(f"Code successfully pushed and merged into '{target_branch}' branch in {repo_key}.")
        logging.info(f"Code successfully pushed and merged into '{target_branch}' branch in {repo_key}.")

    except subprocess.CalledProcessError as e:
        logging.error(f"Error during Git operations in {repo_key}: {e}")
        await update.callback_query.message.reply_text(f"Failed during Git operation in {repo_key}: {e}")


# Add the function to capture and send a screenshot

def resize_image(input_path, output_path, max_size=(1280, 720)):
    with Image.open(input_path) as img:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        img.save(output_path, "PNG")

async def capture_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.callback_query.from_user.username
    if not is_user_allowed(username):
        await update.callback_query.message.reply_text('You are not authorized to use this bot.')
        return

    try:
        await update.callback_query.message.reply_text('📸 Taking a screenshot...')
        
        # Capture the screenshot
        screenshot_path = "/tmp/screenshot.png"
        subprocess.run(['screencapture', '-xC', screenshot_path], check=True)

        # Resize the screenshot to ensure it fits within Telegram's limits
        resized_screenshot_path = "/tmp/screenshot_resized.png"
        resize_image(screenshot_path, resized_screenshot_path)

        await update.callback_query.message.reply_text('🖼️ Screenshot taken! Sending it to you...')

        with open(resized_screenshot_path, 'rb') as screenshot_file:
            retries = 3
            for attempt in range(retries):
                try:
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=screenshot_file)
                    await update.callback_query.message.reply_text('✅ Screenshot sent successfully!')
                    break
                except RetryAfter as e:
                    logging.error(f"Flood control exceeded. Retrying in {e.retry_after} seconds...")
                    await asyncio.sleep(e.retry_after)
                except NetworkError as e:
                    logging.error(f"Network error occurred: {e}. Retrying...")
                    await asyncio.sleep(5)  # Wait a bit before retrying
                except Exception as e:
                    logging.error(f"Error while sending screenshot: {e}")
                    await update.callback_query.message.reply_text('❌ Failed to send screenshot.')
                    break

        # Clean up the temporary files
        os.remove(screenshot_path)
        os.remove(resized_screenshot_path)

    except subprocess.TimeoutExpired:
        logging.error("Screenshot process timed out.")
        await update.callback_query.message.reply_text('❌ Screenshot timed out.')
    except Exception as e:
        logging.error(f"Error while capturing screenshot: {e}")
        await update.callback_query.message.reply_text('❌ Failed to capture screenshot.')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.callback_query.from_user.username
    if not is_user_allowed(username):
        await update.callback_query.message.reply_text('You are not authorized to use this bot.')
        return

    query = update.callback_query
    try:
        await query.answer()
    except BadRequest as e:
        logging.error(f"Error answering query: {e}")

    if query.data.startswith('start_'):
        command = query.data.split('_')[1]
        await run_script(update, context, command)
    elif query.data == 'snap':  # Handle the new snap button
        await capture_screenshot(update, context)
    elif query.data == 'toggle_bluetooth':
        await toggle_bluetooth_device(update, context)
    elif query.data == 'turn_on_airplane_mode':
        await control_airplane_mode(update, context, 'on')
    elif query.data == 'toggle_volume':
        await toggle_volume(update, context)
    elif query.data == 'toggle_timezone':
        await toggle_timezone(update, context)
    elif query.data == 'kill_all_apps':
        await kill_all_apps(update, context)
    elif query.data.startswith('push_code_'):
        repo_key = query.data.split('_')[-1]
        await push_code(update, context, repo_key)  # Dynamic repository push code
    elif query.data == 'stop':
        await stop_script(update, context)
    elif query.data == 'stop_bot':
        await stop_bot(update, context)

def main():
    logging.info("Starting the bot...")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))

    application.run_polling()

    logging.info("Bot has stopped")

if __name__ == '__main__':
    main()
