# Ubuntu Quick User Switcher

A modern GTK4/Libadwaita application for fast user switching on Ubuntu and other Linux distributions. Switch between user accounts without logging out, preserving your current session and applications.

![Quick Switch Screenshot](https://img.shields.io/badge/GTK-4.0-blue) ![Python](https://img.shields.io/badge/Python-3.8+-green) ![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04+-orange)

## Features

🚀 **Intelligent Session Switching**
- Direct switching to users with active sessions (no password required)
- Preserves your current session and running applications
- Smart detection of existing user sessions using systemd loginctl

👤 **Modern User Interface**
- Clean GTK4/Libadwaita design following GNOME HIG
- Profile picture support from AccountsService and ~/.face
- User-friendly confirmation dialogs and status messages

⚡ **Multiple Switching Methods**
- `loginctl activate` - Direct session activation (fastest)
- `dm-tool switch-to-user` - LightDM integration
- GDM D-Bus interface - Native GNOME support
- Fallback to login screen for new users

🔒 **Session Preservation**
- Your current session stays active in the background
- All applications continue running
- Return to your work exactly where you left off

## Installation

### Quick Install
```bash
git clone https://github.com/ecappa/ubuntuQuickUserSwitcher.git
cd ubuntuQuickUserSwitcher
chmod +x install.sh
./install.sh
```

### Manual Installation
```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-4.0 libadwaita-1-dev gir1.2-adw-1

# Install Python dependencies
pip3 install -r requirements.txt

# Make executable
chmod +x quick_switch.py

# Create desktop shortcut (optional)
cp quick-switch.desktop ~/.local/share/applications/
```

## Usage

### Run from Command Line
```bash
./quick_switch.py
```

### Run from Applications Menu
After installation, search for "Quick Switch" in your applications menu.

### How It Works

1. **Launch** the application
2. **Select** a user from the list
3. **Confirm** the switch
4. The app will:
   - Switch directly to active sessions (instant)
   - Open login screen for new users
   - Preserve your current session

## Requirements

- **OS**: Ubuntu 20.04+ (or any Linux with systemd)
- **Python**: 3.8+
- **Desktop**: GTK4-compatible environment (GNOME, etc.)
- **Display Manager**: GDM, LightDM, or compatible

## Technical Details

### Session Detection
- Uses `loginctl list-sessions` to detect active user sessions
- Parses session state, user ID, and session ID
- Intelligently chooses switching method based on session status

### Switching Methods (Priority Order)
1. **loginctl activate [session-id]** - For existing sessions
2. **dm-tool switch-to-user [username]** - LightDM direct switching
3. **GDM D-Bus interface** - Native GNOME switching
4. **dm-tool switch-to-greeter** - Fallback to login screen

### Profile Pictures
Searches for user avatars in:
1. `/var/lib/AccountsService/icons/[username]`
2. `~/.face`
3. `~/.face.{jpg,jpeg,png,gif}`

## Troubleshooting

### User Switching Doesn't Work
- Ensure your display manager supports user switching
- Check that systemd-logind is running: `systemctl status systemd-logind`
- Verify loginctl works: `loginctl list-sessions`

### Permission Issues
- Make sure the script is executable: `chmod +x quick_switch.py`
- Check that your user has access to loginctl commands

### Display Issues
- Ensure GTK4 and Libadwaita are installed
- Update your system: `sudo apt update && sudo apt upgrade`

## Development

### Project Structure
- `quick_switch.py` - Main application
- `requirements.txt` - Python dependencies
- `install.sh` - Installation script
- `quick-switch.desktop` - Desktop entry
- `CLAUDE.md` - Development documentation

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on Ubuntu/GNOME
5. Submit a pull request

## License

This project is open source. Feel free to use, modify, and distribute.

## Credits

Developed with assistance from [Claude Code](https://claude.ai/code) for modern Ubuntu user switching needs.