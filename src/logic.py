"""
    Tuxus - ISO burning & USB drive formatting app for Linux
    Copyright © 2025 santofrancesco
    Full notice can be found on https://www.github.com/santofrancesco/tuxus/blob/main/LICENSE

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import subprocess, json, os, re
from gi.repository import GLib

# Run shell command, handle errors, and optionally update status label
def run_cmd(cmd, status_label=None, critical=True, **kwargs):
    """
    Run a shell command with subprocess.

    Args:
        cmd (list): Command and arguments as list, e.g. ["lsblk", "-J"].
        status_label (Gtk.Label, optional): Label to display messages in GUI.
        critical (bool): If True, failures raise CalledProcessError.
                         If False, return the exit code instead.
        kwargs: Extra arguments passed to subprocess.run.

    Returns:
        - If critical=True: completed process (raises on error).
        - If critical=False: returncode (int).
    """
    try:
        if critical:
            result = subprocess.run(
                cmd, check=True, text=True, capture_output=True, **kwargs
            )
            return result
        else:
            result = subprocess.run(cmd, text=True, capture_output=True, **kwargs)
            return result.returncode

    except subprocess.CalledProcessError as e:
        msg = (
            f"Command failed:\n{' '.join(cmd)}\n\n"
            f"Exit code: {e.returncode}\n"
            f"Error: {e.stderr.strip() if e.stderr else 'No message'}"
        )
        if status_label:
            GLib.idle_add(status_label.set_text, msg)
        else:
            print(msg)
        raise


# File filter for selecting ISO images
def iso_filter():
    from gi.repository import Gtk

    file_filter = Gtk.FileFilter()
    file_filter.set_name("ISO images")
    file_filter.add_pattern("*.iso")
    return file_filter


# Returns device model string for a given device path
def get_vendor_model(device_path):
    try:
        result = run_cmd(
            ["lsblk", "-J", "-o", "MODEL", device_path],
            status_label=None,
            critical=True,
        )
        data = json.loads(result.stdout)
        dev_info = data["blockdevices"][0]
        model = (dev_info.get("model") or "UnknownModel").strip()
        return f"{model.replace(' ', '_')}"
    except Exception:
        return "UnknownModel"


# Lists removable USB drives with model, label, size, and path
def list_usb_drives():
    try:
        result = run_cmd(
            ["lsblk", "-J", "-o", "NAME,RM,SIZE,MODEL,VENDOR,LABEL"],
            status_label=None,
            critical=True,
        )
        devices = json.loads(result.stdout)
        return [
            {
                "device": f"/dev/{d['name']}",
                "model": f"{d.get('vendor','').strip()} {d.get('model','').strip()}".strip(),
                "label": (d.get("label") or "").strip(),
                "size": d.get("size", "?"),
            }
            for d in devices["blockdevices"]
            if d["rm"]
        ]
    except Exception as e:
        print("Error listing drives:", e)
        return []


# Refreshes combo box with currently available USB drives
def refresh_drives(combo, drives_map=None):
    combo.remove_all()
    drives = list_usb_drives()
    if drives_map is not None:
        drives_map.clear()

    if not drives:
        combo.append_text("No USB drives found")
    else:
        for idx, d in enumerate(drives):
            label = f"{d['label']} {d['model']} ({d['size']}) - {d['device']}"
            combo.append_text(label)
            if drives_map is not None:
                drives_map[idx] = d
    combo.set_active(0)


# Extracts /dev/... path from drive info string
def extract_device_path(drive_info):
    match = re.search(r"(/dev/\w+)", drive_info)
    return match.group(1) if match else None


# =====================================================
#  Burn ISO
# =====================================================

# Checks if ISO path and drive selection are valid
def is_burn_ready(iso_path, drive_info):
    return bool(iso_path and drive_info and "No USB" not in drive_info)


# Writes ISO image to USB drive using dd, updating progress bar
def write_iso(iso, drive_info, status_label, progressbar):
    device_path = extract_device_path(drive_info)
    if not device_path:
        GLib.idle_add(status_label.set_text, "Error: Could not determine device path.")
        return

    total_size = os.path.getsize(iso)

    try:
        unmount_drive(device_path)
        cmd = [
            "pkexec",
            "dd",
            f"if={iso}",
            f"of={device_path}",
            "bs=4M",
            "status=progress",
            "oflag=sync",
        ]
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)

        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            if not line:
                continue
            if "bytes" in line and "copied" in line:
                try:
                    copied = int(line.split()[0])
                    fraction = copied / total_size
                    GLib.idle_add(progressbar.set_fraction, min(fraction, 1.0))
                    GLib.idle_add(progressbar.set_text, f"{fraction:.0%}")
                except ValueError:
                    pass

        if process.returncode == 0:
            GLib.idle_add(status_label.set_text, "Write complete")
            GLib.idle_add(progressbar.set_fraction, 1.0)
            GLib.idle_add(progressbar.set_text, "100%")
        else:
            GLib.idle_add(status_label.set_text, f"Error (exit {process.returncode})")

    except Exception as e:
        GLib.idle_add(status_label.set_text, f"Error: {e}")


# =====================================================
#  Format USB
# =====================================================

# Unmounts drive and its partitions if they are mounted
def unmount_drive(device_path):
    try:
        result = run_cmd(
            ["lsblk", "-J", "-o", "NAME,MOUNTPOINT", device_path],
            status_label=None,
            critical=True,
        )
        devices = json.loads(result.stdout)["blockdevices"]
        for d in devices:
            if d.get("mountpoint"):
                run_cmd(
                    ["pkexec", "umount", d["mountpoint"]],
                    status_label=None,
                    critical=False,
                )
            for part in d.get("children", []):
                if part.get("mountpoint"):
                    run_cmd(
                        ["pkexec", "umount", part["mountpoint"]],
                        status_label=None,
                        critical=False,
                    )
    except Exception as e:
        print(f"Unmount error: {e}")


# Handles full formatting workflow: unmount, format, update GUI status
def run_format(drive_info, fs, label, cluster_size, status_label, progressbar):

    device_path = extract_device_path(drive_info)
    success = False

    if not device_path:
        GLib.idle_add(status_label.set_text, "Error: Could not determine device path.")
        return
    try:
        unmount_drive(device_path)
        success = format_drive(device_path, fs, label, cluster_size, status_label)
        if success:
            GLib.idle_add(status_label.set_text, "Format complete")
        else:
            GLib.idle_add(status_label.set_text, "Format failed")

    except Exception as e:
        GLib.idle_add(status_label.set_text, f"Format error: {e}")

    finally:
        # Stop the pulsing bar
        def stop_pulse():
            if hasattr(progressbar, "_pulse_id"):
                GLib.source_remove(progressbar._pulse_id)
                delattr(progressbar, "_pulse_id")
            progressbar.set_fraction(1.0 if success else 0.0)
            return False

        GLib.idle_add(stop_pulse)


# Formats drive with given filesystem, label, and cluster size
def format_drive(device_path, fs, label, cluster_size, status_label):
    try:
        # Ensure cluster_size is an integer
        cluster_size = int(cluster_size)

        # Define allowed cluster sizes
        valid_clusters = {
            "FAT32": [512, 1024, 2048, 4096, 8192, 16384, 32768, 65536],
            "exFAT": [512, 1024, 2048, 4096, 8192, 16384, 32768, 65536],
            "NTFS": [512, 1024, 2048, 4096, 8192, 16384, 32768, 65536],
            "ext4": [1024, 2048, 4096],
        }

        if fs not in valid_clusters:
            raise ValueError(f"Unsupported filesystem: {fs}")

        if cluster_size not in valid_clusters[fs]:
            raise ValueError(f"Invalid cluster size {cluster_size} for {fs}")

        cmd = ["pkexec"]

        if fs == "FAT32":
            cluster_tmp = cluster_size / 512
            cmd += [
                "/usr/sbin/mkfs.vfat",
                "-F",
                "32",
                "-I",
                "-n",
                label,
                "-s",
                str(int(cluster_tmp)),
                device_path,
            ]

        elif fs == "exFAT":
            cmd += ["mkfs.exfat", "-L", label, "-c", str(cluster_size), device_path]

        elif fs == "NTFS":
            run_cmd(
                ["pkexec", "parted", "-s", device_path, "mklabel", "gpt"],
                status_label=status_label,
                critical=True,
            )
            run_cmd(
                [
                    "pkexec",
                    "parted",
                    "-s",
                    device_path,
                    "mkpart",
                    "primary",
                    "ntfs",
                    "0%",
                    "100%",
                ],
                status_label=status_label,
                critical=True,
            )
            part_path = device_path + "1"
            cmd += ["mkfs.ntfs", "-f", "-L", label, "-c", str(cluster_size), part_path]

        elif fs == "ext4":
            cmd += ["mkfs.ext4", "-L", label, "-b", str(cluster_size), device_path]

        else:
            raise ValueError("Unsupported filesystem")

        try:
            run_cmd(cmd, status_label=status_label, critical=True)
            GLib.idle_add(status_label.set_text, "Format complete.")
            return True
        except subprocess.CalledProcessError:
            # Error already shown in status_label
            return False

    except Exception as e:
        msg = f"Format error: {e}"
        if status_label:
            GLib.idle_add(status_label.set_text, msg)
        else:
            print(msg)
        return False


# =====================================================
#  Verify Hash
# =====================================================

# Verifies file hash against user input using chosen algorithm
def verify_hash(file_path, algo, user_hash, status_label):
    try:
        algo_map = {
            "MD5": "md5sum",
            "SHA-1": "sha1sum",
            "SHA-256": "sha256sum",
            "SHA-512": "sha512sum",
        }
        cmd = [algo_map[algo], file_path]
        result = run_cmd(cmd, status_label=status_label, critical=True)
        computed_hash = result.stdout.split()[0].lower()

        if computed_hash == user_hash:
            GLib.idle_add(
                status_label.set_markup,
                f"<span foreground='green'><b>✅ Hash matches!</b></span>\n"
                f"<small>Computed hash: {computed_hash}</small>",
            )
        else:
            GLib.idle_add(
                status_label.set_markup,
                f"<span foreground='red'><b>❌ Hash does not match.</b></span>\n"
                f"<small>Computed hash: {computed_hash}</small>",
            )
    except Exception as e:
        GLib.idle_add(status_label.set_text, f"Error verifying hash: {e}")
