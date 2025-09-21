# TUXUS  
*A clean and powerful ISO burning app & USB drive formatting for Linux.*

![Linux](https://img.shields.io/badge/Linux-FCC624?logo=linux&logoColor=black)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)

---

## 💿 About TUXUS
TUXUS is a lightweight Python GTK application that makes it effortless to prepare USB drives and burn ISO images.  
Whether you’re flashing a Linux distribution or just reformatting a drive, TUXUS provides a modern interface with essential power-user features.

---

## 📀 Features
- Format drives with **FAT32, NTFS, exFAT, ext4**
- Burn ISO images directly to USB drives
- Verify file integrity with multiple hash algorithms
- User-friendly GTK interface with confirmation dialogs
- Smart options: filesystem label length checks, cluster size, and more

---

## 🛠️ Installation

### Option 1: Install via `.deb` package (recommended for most users)

Download the latest `.deb` release from the [Releases page](github.com/santofrancesco/tuxus/releases) and install it with:
```bash
sudo dpkg -i tuxus_x.y.z.deb    # replace x.y.z with the version you want to install
sudo apt-get install -f   # to resolve any missing dependencies
```

After installation, you can launch TUXUS from your application menu or by running:
```bash
tuxus
```

### Option 2: Run from source (for developers)

Clone the repository:
```bash
git clone https://github.com/yourusername/tuxus.git
cd tuxus
```

Install Python dependencies:
```bash
pip install -r requirements.txt
```

Run the application:
```bash
python3 main.py
```

---

## 📸 Screenshots

---

## 📖 License
(work in progress)
