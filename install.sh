#!/bin/bash

# Install system dependencies
sudo apt update
sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-4.0 libadwaita-1-dev gir1.2-adw-1

# Make the application executable
chmod +x quick_switch.py

# Create desktop shortcut
chmod +x quick-switch.desktop
cp quick-switch.desktop ~/Bureau/ 2>/dev/null || cp quick-switch.desktop ~/Desktop/ 2>/dev/null

# Install to applications menu
mkdir -p ~/.local/share/applications
cp quick-switch.desktop ~/.local/share/applications/

echo "Installation complete!"
echo "- Desktop shortcut created"
echo "- Application available in menu"
echo "- Run with: ./quick_switch.py"