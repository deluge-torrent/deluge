FROM ubuntu:22.04

# Use HEREDOC to avoid creating multiple layers
RUN <<EOF
# Update the package list
apt-get update

export DEBIAN_FRONTEND=noninteractive

# install generic python3 packages
apt-get install -y \
    build-essential \
    curl \
    git \
    locales \
    python3 \
    python3-pip \
    pipx

# Install pipx and fix PATH
pipx install tox
echo "" >> /root/.bashrc
echo "# Add pipx binaries to PATH" >> /root/.bashrc
echo "export PATH=/root/.local/bin:\$PATH" >> /root/.bashrc

# Install prerequisites per 01-setup.md
apt-get install -y \
    intltool closure-compiler
apt-get install -y \
    python3-libtorrent python3-geoip python3-dbus  python3-gi \
    python3-gi-cairo gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 python3-pygame libnotify4 \
    librsvg2-common xdg-utils

apt-get install -y sudo
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 1
#pip install --upgrade pip wheel setuptools
#pip install -r requirements-ci.txt

# Clean up the package list to save space in the layer (~54MB)
#rm -rf /var/lib/apt/lists/*

EOF

# Set the working directory
#WORKDIR /app

# Copy the current directory contents into the container at /app
#COPY . /app

# Specify the command to run on container start
CMD ["bash"]
