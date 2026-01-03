# Ubuntu Router Deployment Guide

This guide will walk you through deploying the Ubuntu Router Manager on your server using MobaXterm.

## Prerequisites

1.  **Ubuntu Server**: A machine (or VM) running Ubuntu Server (20.04 or 22.04 LTS recommended).
2.  **MobaXterm**: Installed on your Windows PC.
3.  **Network Connection**: You must be able to ping your Ubuntu server's IP address.

---

## Step 1: Connect to your Server

1.  Open **MobaXterm**.
2.  Click on the **Session** button (top left).
3.  Choose **SSH**.
4.  **Remote host**: Enter your Ubuntu server's IP address (e.g., `192.168.1.100`).
5.  **Specify username**: Check this box and enter your username (usually `root` or `ubuntu`).
6.  Click **OK**.
7.  Enter your password when prompted.

---

## Step 2: Transfer Project Files

You have two options to get the code onto your server.

### Option A: Using Git (Recommended)

If your server has internet access, this is the easiest way.

1.  In the MobaXterm terminal, run:
    ```bash
    sudo apt update
    sudo apt install -y git
    ```
2.  Clone the repository:
    ```bash
    git clone https://github.com/cjtech91/ubunturouter.git
    # Note: The directory name might be 'ubuntu-router' or 'ubunturouter' depending on the URL
    cd ubuntu-router || cd ubunturouter
    ```
    *(Replace `<YOUR_REPOSITORY_URL>` with the actual URL of your git repo).*

### Option B: Using MobaXterm SFTP (If you have the files locally)

1.  On the left side of MobaXterm, you will see the **SFTP** browser pane.
2.  Navigate to your home directory (e.g., `/home/your_username/`) or `/opt/`.
3.  Drag and drop the entire `ubuntu-router` folder from your Windows PC into this pane.
4.  In the terminal, enter the directory:
    ```bash
    cd ubuntu-router
    ```

---

## Step 3: Run the Automated Installer

We have prepared a script that installs all necessary dependencies (Python, Flask, DHCP server, PPPoE server, etc.) and sets up the web dashboard to run automatically.

1.  Make the script executable:
    ```bash
    chmod +x scripts/install.sh
    ```

2.  Run the installer:
    ```bash
    ./scripts/install.sh
    ```

3.  **Wait for completion**. The script will:
    *   Update your system packages.
    *   Install system tools (`netplan`, `isc-dhcp-server`, `pppoe`).
    *   Install Python libraries.
    *   Create a systemd service named `ubuntu-router`.
    *   Start the web server.

---

## Step 4: Access the Dashboard

Once the installation finishes, the script will show you the IP address to access.

1.  Open your web browser (Chrome, Firefox, Edge).
2.  Enter the URL:
    ```
    http://<YOUR_SERVER_IP>
    ```
    *(Example: `http://192.168.1.100`)*

3.  You should see the **Ubuntu Router Dashboard**.

---

## Step 5: Post-Installation & Usage

### Applying Configurations
When you make changes in the dashboard (e.g., changing LAN IP, adding Load Balancing weights), the changes are saved to a file but **not applied immediately** to the system to prevent network dropouts.

1.  Go to the Dashboard or any config page.
2.  Click the green **"Apply Configuration to System"** button at the top right.
3.  This will restart the necessary services on the server.

### Troubleshooting

**If the dashboard doesn't load:**
Check the status of the service in your SSH terminal:
```bash
sudo systemctl status ubuntu-router
```

**If you need to see logs:**
```bash
sudo journalctl -u ubuntu-router -f
```

**To restart the application manually:**
```bash
sudo systemctl restart ubuntu-router
```
