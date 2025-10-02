#!/usr/bin/env python3

import gi
import os
import pwd
import subprocess
import sys
import re
import shlex
import logging
from pathlib import Path

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GdkPixbuf, Gio, GLib

# Configuration constants
ACCOUNTS_SERVICE_ICONS_PATH = '/var/lib/AccountsService/icons'
DEFAULT_HOME_PREFIX = '/home/'
USERNAME_MAX_LENGTH = 32

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UserSwitcher(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Quick Switch")
        self.set_default_size(400, 500)

        # Main container with header bar
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Create header bar as first child
        header = Adw.HeaderBar()
        main_box.append(header)

        # Title
        title_label = Gtk.Label()
        title_label.set_markup('<big><b>Switch User</b></big>')
        title_label.set_margin_top(20)
        title_label.set_margin_bottom(20)
        main_box.append(title_label)

        # Scrolled window for user list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)

        # List box for users
        self.user_listbox = Gtk.ListBox()
        self.user_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.user_listbox.add_css_class("boxed-list")
        self.user_listbox.connect("row-activated", self.on_user_selected)

        scrolled.set_child(self.user_listbox)
        main_box.append(scrolled)

        # Cancel button
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.set_margin_top(20)
        cancel_button.set_margin_bottom(20)
        cancel_button.set_margin_start(20)
        cancel_button.set_margin_end(20)
        cancel_button.connect("clicked", lambda x: self.close())
        main_box.append(cancel_button)

        self.set_content(main_box)

        # Load users
        self.load_users()
    
    def validate_username(self, username):
        """Validate username against POSIX standards"""
        if not username:
            return False
        if len(username) > USERNAME_MAX_LENGTH:
            return False
        # POSIX username regex: starts with letter/underscore, followed by letters, digits, underscore, hyphen, or dollar
        # Also check for control characters and whitespace
        if not re.match(r'^[a-z_]([a-z0-9_-]{0,31}|[a-z0-9_-]{0,30}\$)$', username) or any(c.isspace() or ord(c) < 32 for c in username):
            return False
        return True
    
    def validate_home_path(self, home_dir):
        """Validate that home directory is safe to access"""
        try:
            home_path = Path(home_dir).resolve()
            # Ensure home directory is under /home/ or another safe location
            if not str(home_path).startswith(DEFAULT_HOME_PREFIX):
                return False
            # Ensure it's not a symlink to somewhere dangerous
            if home_path.is_symlink():
                # Additional validation could be added here for symlinks
                pass
            return True
        except (OSError, ValueError):
            return False

    def get_profile_picture(self, username, home_dir):
        """Get user profile picture from various locations"""
        # Validate username and home directory before proceeding
        if not self.validate_username(username):
            logger.warning(f"Invalid username format: {username}")
            return None
        
        if not self.validate_home_path(home_dir):
            logger.warning(f"Unsafe home directory path: {home_dir}")
            return None
        
        try:
            # Try AccountsService first (public location)
            accounts_path = Path(f"{ACCOUNTS_SERVICE_ICONS_PATH}/{username}")
            if accounts_path.exists():
                return str(accounts_path)

            # Try ~/.face only if accessible and path is safe
            face_path = Path(home_dir) / ".face"
            if face_path.exists():
                return str(face_path)

            # Try common image extensions in home
            for ext in ['.jpg', '.jpeg', '.png', '.gif']:
                face_ext_path = Path(home_dir) / f".face{ext}"
                if face_ext_path.exists():
                    return str(face_ext_path)
        except (PermissionError, OSError) as e:
            # Can't access this user's home directory, skip profile picture
            logger.debug(f"Cannot access profile picture for {username}: {e}")
            pass

        return None

    def create_user_row(self, user_info, is_current_user=False):
        """Create a row for a user"""
        username, fullname, home_dir, uid = user_info

        # Main row container
        row = Adw.ActionRow()
        row.set_title(fullname or username)
        row.set_subtitle(username)
        row.user_data = username
        row.is_current_user = is_current_user

        # Profile picture
        avatar = Adw.Avatar()
        avatar.set_size(48)
        avatar.set_text(username)

        # Try to load profile picture
        pic_path = self.get_profile_picture(username, home_dir)
        if pic_path:
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(pic_path, 48, 48, True)
                avatar.set_custom_image(pixbuf)
            except (GLib.Error, OSError) as e:
                logger.warning(f"Failed to load profile picture for {username}: {e}")
                # Use default avatar if image loading fails

        row.add_prefix(avatar)

        if is_current_user:
            # Current user styling - add label instead of arrow
            current_label = Gtk.Label(label="(Current)")
            current_label.add_css_class("dim-label")
            row.add_suffix(current_label)
            row.set_sensitive(False)  # Disable clicking
        else:
            # Add arrow icon and hover effect
            arrow = Gtk.Image.new_from_icon_name("go-next-symbolic")
            row.add_suffix(arrow)
            row.set_activatable(True)

        return row

    def load_users(self):
        """Load system users and populate the list"""
        users = []
        current_user = os.getenv('USER')

        # Get all users from /etc/passwd
        for user in pwd.getpwall():
            username = user.pw_name
            uid = user.pw_uid
            home_dir = user.pw_dir
            gecos = user.pw_gecos
            shell = user.pw_shell

            # Skip system users (UID < 1000)
            if uid < 1000:
                continue

            # Skip users with no shell or system shells
            if not shell or shell in ['/usr/sbin/nologin', '/bin/false', '/usr/bin/false']:
                continue

            # Validate username format for security
            if not self.validate_username(username):
                logger.warning(f"Skipping user with invalid username format: {username}")
                continue

            # Extract full name from GECOS field
            fullname = gecos.split(',')[0] if gecos else username

            users.append((username, fullname, home_dir, uid))

        # Sort users by full name
        users.sort(key=lambda x: x[1].lower())

        # Add users to list
        for user_info in users:
            username = user_info[0]
            is_current = username == current_user
            row = self.create_user_row(user_info, is_current)
            self.user_listbox.append(row)

    def on_user_selected(self, listbox, row):
        """Handle user selection"""
        # Skip if current user
        if hasattr(row, 'is_current_user') and row.is_current_user:
            return

        username = row.user_data
        
        # Additional security validation
        if not self.validate_username(username):
            error_dialog = Adw.MessageDialog.new(self)
            error_dialog.set_heading("Invalid User")
            error_dialog.set_body(f"Selected user '{username}' has an invalid format.")
            error_dialog.add_response("ok", "OK")
            error_dialog.present()
            return

        # Confirm switch
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Switch User")
        dialog.set_body(f"Switch to user '{username}'?")
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("switch", "Switch")
        dialog.set_response_appearance("switch", Adw.ResponseAppearance.SUGGESTED)

        dialog.connect("response", self.on_confirm_switch, username)
        dialog.present()

    def get_user_sessions(self):
        """Get list of active user sessions"""
        try:
            result = subprocess.run(['loginctl', 'list-sessions', '--no-legend'],
                                  capture_output=True, text=True, check=True)
            sessions = {}
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        session_id = parts[0]
                        uid = parts[1]
                        username = parts[2]
                        state = parts[5] if len(parts) > 5 else "unknown"
                        sessions[username] = {
                            'session_id': session_id,
                            'uid': uid,
                            'state': state
                        }
            return sessions
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {}

    def on_confirm_switch(self, dialog, response, username):
        """Handle switch confirmation with intelligent session switching"""
        if response == "switch":
            # Additional security validation
            if not self.validate_username(username):
                error_dialog = Adw.MessageDialog.new(self)
                error_dialog.set_heading("Security Error")
                error_dialog.set_body("Invalid username format detected.")
                error_dialog.add_response("ok", "OK")
                error_dialog.present()
                return
            
            # First, get active sessions
            sessions = self.get_user_sessions()
            user_has_session = username in sessions

            success = False

            if user_has_session:
                # User has an active session - switch directly
                session_id = sessions[username]['session_id']
                # Safely quote username for shell commands
                safe_username = shlex.quote(username)
                methods = [
                    # Method 1: Activate existing session (most reliable)
                    (['loginctl', 'activate', session_id], f"Activate existing session {session_id}"),

                    # Method 2: Switch to user with dm-tool (username is safe, but quote for consistency)
                    (['dm-tool', 'switch-to-user', safe_username], "LightDM direct switch"),

                    # Method 3: GDM D-Bus for existing session (username is safe, but quote for consistency)
                    (['dbus-send', '--system', '--type=method_call',
                      '--dest=org.freedesktop.DisplayManager',
                      '/org/freedesktop/DisplayManager/Seat0',
                      'org.freedesktop.DisplayManager.Seat.SwitchToUser',
                      f'string:{safe_username}', 'string:'], "GDM D-Bus switch"),
                ]

                for method, description in methods:
                    try:
                        logger.debug(f"Trying {description} for existing session...")
                        subprocess.run(method, check=True, capture_output=True, timeout=5)
                        logger.info(f"Success with {description}")
                        success = True
                        self.close()
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
                        logger.warning(f"Failed {description}: {e}")
                        continue

            if not success:
                # No active session or direct switch failed - use greeter
                greeter_methods = [
                    # Method 1: dm-tool greeter (most compatible)
                    (['dm-tool', 'switch-to-greeter'], "Switch to login screen"),

                    # Method 2: Lock current session first
                    (['loginctl', 'lock-session'], "Lock and switch"),
                ]

                for method, description in greeter_methods:
                    try:
                        logger.debug(f"Trying {description}...")
                        subprocess.run(method, check=True, capture_output=True, timeout=5)

                        # If locking session, also switch to greeter
                        if 'lock-session' in method:
                            subprocess.run(['dm-tool', 'switch-to-greeter'], check=True, timeout=5)

                        success = True

                        # Show info about what happened
                        if user_has_session:
                            info_text = f"Session switch failed. Opened login screen.\nUser '{username}' has an active session but couldn't switch directly."
                        else:
                            info_text = f"Opened login screen for user '{username}'.\nThis user needs to login for the first time."

                        logger.info(f"Successfully opened login screen for user {username}")
                        info_dialog = Adw.MessageDialog.new(self)
                        info_dialog.set_heading("Login Screen Opened")
                        info_dialog.set_body(info_text)
                        info_dialog.add_response("ok", "OK")
                        info_dialog.present()

                        self.close()
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
                        logger.warning(f"Failed {description}: {e}")
                        continue

            # If everything failed
            if not success:
                logger.error(f"Failed to switch to user '{username}' - all methods exhausted")
                error_dialog = Adw.MessageDialog.new(self)
                error_dialog.set_heading("Switch Failed")
                error_dialog.set_body(f"Unable to switch to user '{username}' or open login screen.\nTry using the system's built-in user switcher.")
                error_dialog.add_response("ok", "OK")
                error_dialog.present()

class QuickSwitchApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='com.quickswitch.app')

    def do_activate(self):
        win = self.get_active_window()
        if not win:
            win = UserSwitcher(application=self)
        win.present()

def main():
    app = QuickSwitchApp()
    return app.run(sys.argv)

if __name__ == '__main__':
    main()