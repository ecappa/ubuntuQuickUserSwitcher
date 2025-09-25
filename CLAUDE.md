# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QuickSwitch is a Python GTK4/Libadwaita application for switching between user accounts on Linux systems. The app provides a modern GUI interface showing all system users with profile pictures and allows switching users through various Linux session management methods.

## Development Environment

### Dependencies
- Python 3 with GTK4 bindings (pygobject>=3.42.0)
- System packages: python3-gi, python3-gi-cairo, gir1.2-gtk-4.0, libadwaita-1-dev, gir1.2-adw-1
- Install dependencies: `./install.sh`

### Running the Application
- Direct execution: `./quick_switch.py`
- The install script creates desktop shortcuts and menu entries

## Architecture

### Core Components
- `UserSwitcher`: Main Adw.ApplicationWindow that displays user list and handles switching
- `QuickSwitchApp`: Adw.Application wrapper for the main window
- User data sourced from `/etc/passwd` with filtering for regular users (UID >= 1000)

### User Switching Methods
The app attempts multiple fallback methods for user switching:
1. `gnome-session-quit --logout --no-prompt` (modern GNOME)
2. `gdm-flexiserver` (GDM legacy)
3. `loginctl unlock-session` + `dm-tool switch-to-greeter` (systemd/LightDM)

### Profile Picture Resolution
Profile pictures are loaded from multiple sources in priority order:
1. `/var/lib/AccountsService/icons/{username}` (system-wide)
2. `~/.face` (user home directory)
3. `~/.face.{jpg,jpeg,png,gif}` (user home with extensions)

## File Structure
- `quick_switch.py`: Main application code
- `requirements.txt`: Python dependencies
- `install.sh`: System setup and installation script
- `quick-switch.desktop`: Desktop entry file