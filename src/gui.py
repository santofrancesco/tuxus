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

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import logic

# Main application window with tabs for burning, formatting, and verifying hashes
class Tuxus(Gtk.Window):

    # Initialize window and build UI layout
    def __init__(self):
        super().__init__(title="Tuxus")

        # Define window size
        self.set_border_width(10)
        self.set_default_size(600, 400)

        # Set app logo (icon)
        self.set_icon_from_file("icons/cd_fire.svg")

        # Main vertical box to hold notebook + footer
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.add(vbox)

        notebook = Gtk.Notebook()
        vbox.pack_start(notebook, True, True, 0)

        # Map of index → drive info for format tab
        self.format_drives_map = {}

        # =====================================================
        # TAB 1: Burn ISO
        # =====================================================
        burn_tab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        burn_tab.set_border_width(15)

        burn_drive_list = Gtk.Label()
        burn_drive_list.set_markup("<b>Select a USB drive:</b>")
        burn_drive_list.set_xalign(0)
        burn_tab.pack_start(burn_drive_list, False, False, 5)

        # Horizontal box for drive dropdown + refresh button
        drive_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.drive_combo = Gtk.ComboBoxText()
        self.drive_combo.set_hexpand(True)
        drive_row.pack_start(self.drive_combo, True, True, 0)

        refresh_burn_btn = Gtk.Button()
        refresh_burn_btn.set_tooltip_text("Refresh drives")
        icon = Gtk.Image.new_from_icon_name(
            "view-refresh-symbolic", Gtk.IconSize.BUTTON
        )
        refresh_burn_btn.set_image(icon)
        refresh_burn_btn.connect("clicked", self.on_refresh_burn)
        drive_row.pack_start(refresh_burn_btn, False, False, 0)
        drive_row.set_margin_bottom(20)
        burn_tab.pack_start(drive_row, False, False, 0)

        # ISO selector
        iso_label = Gtk.Label()
        iso_label.set_markup("<b>Select an ISO image:</b>")
        iso_label.set_xalign(0)
        burn_tab.pack_start(iso_label, False, False, 5)

        self.iso_button = Gtk.FileChooserButton(
            title="Select ISO", action=Gtk.FileChooserAction.OPEN
        )
        self.iso_button.set_filter(logic.iso_filter())
        self.iso_button.set_margin_bottom(20)
        burn_tab.pack_start(self.iso_button, False, False, 0)

        # Connect signals for validation
        self.iso_button.connect("file-set", self.check_burn_ready)
        self.drive_combo.connect("changed", self.check_burn_ready)

        # Start button
        self.start_button = Gtk.Button(label="Write to USB")
        self.start_button.set_sensitive(False)
        self.start_button.set_halign(Gtk.Align.CENTER)
        self.start_button.set_margin_top(20)
        self.start_button.connect("clicked", self.on_start_clicked)
        burn_tab.pack_start(self.start_button, False, False, 0)

        # Progress bar
        self.progressbar = Gtk.ProgressBar()
        self.progressbar.set_show_text(True)
        self.progressbar.set_margin_top(0)
        burn_tab.pack_end(self.progressbar, False, False, 0)

        # Status
        self.status = Gtk.Label(label="")
        burn_tab.pack_end(self.status, False, False, 20)

        notebook.append_page(burn_tab, Gtk.Label(label="Burn ISO"))

        # =====================================================
        # TAB 2: Format USB
        # =====================================================
        format_tab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        format_tab.set_border_width(15)

        format_drive_list = Gtk.Label()
        format_drive_list.set_markup("<b>Select a USB drive:</b>")
        format_drive_list.set_xalign(0)
        format_tab.pack_start(format_drive_list, False, False, 5)

        # Horizontal box for drive dropdown + refresh button
        format_drive_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.format_drive_combo = Gtk.ComboBoxText()
        self.format_drive_combo.set_hexpand(True)
        format_drive_row.pack_start(self.format_drive_combo, True, True, 0)

        refresh_format_btn = Gtk.Button()
        refresh_format_btn.set_tooltip_text("Refresh drives")
        icon2 = Gtk.Image.new_from_icon_name(
            "view-refresh-symbolic", Gtk.IconSize.BUTTON
        )
        refresh_format_btn.set_image(icon2)
        refresh_format_btn.connect("clicked", self.on_refresh_format)
        format_drive_row.pack_start(refresh_format_btn, False, False, 0)
        format_drive_row.set_margin_bottom(20)
        format_tab.pack_start(format_drive_row, False, False, 0)

        # Volume label
        label_label = Gtk.Label()
        label_label.set_markup("<b>New device label:</b>")
        label_label.set_xalign(0)
        format_tab.pack_start(label_label, False, False, 5)

        self.format_label_entry = Gtk.Entry()
        self.format_label_entry.set_placeholder_text("e.g. MY_USB")
        format_tab.pack_start(self.format_label_entry, False, False, 0)

        # Container row for both filesystem and cluster size
        fs_cluster_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=40)
        fs_cluster_row.set_halign(Gtk.Align.CENTER)

        # Filesystem
        fs_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        fs_column.set_halign(Gtk.Align.CENTER)

        fs_label = Gtk.Label()
        fs_label.set_markup("<b>Filesystem:</b>")
        fs_column.pack_start(fs_label, False, False, 0)

        self.format_fs_combo = Gtk.ComboBoxText()
        self.format_fs_combo.connect("changed", self.on_fs_changed)
        for fs in ["FAT32", "exFAT", "NTFS", "ext4"]:
            self.format_fs_combo.append_text(fs)
        self.format_fs_combo.set_active(0)
        fs_column.pack_start(self.format_fs_combo, False, False, 5)
        fs_cluster_row.pack_start(fs_column, False, False, 0)

        # Cluster size
        cluster_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        cluster_column.set_halign(Gtk.Align.CENTER)

        cluster_label = Gtk.Label()
        cluster_label.set_markup("<b>Cluster size:</b>")
        cluster_column.pack_start(cluster_label, False, False, 0)

        self.format_cluster_combo = Gtk.ComboBoxText()
        for size in ["512", "1024", "2048", "4096", "8192", "16384", "32768", "65536"]:
            self.format_cluster_combo.append_text(size)
        # Set default value to 4096
        self.format_cluster_combo.set_active(3)
        cluster_column.pack_start(self.format_cluster_combo, False, False, 5)
        fs_cluster_row.pack_start(cluster_column, False, False, 0)

        # Add the row to the format tab
        format_tab.pack_start(fs_cluster_row, False, False, 15)

        # Connect signals
        self.format_drive_combo.connect("changed", self.on_format_drive_selected)
        self.format_drive_combo.connect("changed", self.check_format_ready)
        self.format_label_entry.connect("changed", self.check_format_ready)
        self.format_cluster_combo.connect("changed", self.check_format_ready)

        # Format button
        self.format_button = Gtk.Button(label="Format Drive")
        self.format_button.set_sensitive(False)
        self.format_button.set_halign(Gtk.Align.CENTER)
        self.format_button.set_margin_top(20)
        self.format_button.connect("clicked", self.on_format_clicked)
        format_tab.pack_start(self.format_button, False, False, 0)

        # Format progress bar
        self.format_progressbar = Gtk.ProgressBar()
        self.format_progressbar.set_show_text(False)
        self.format_progressbar.set_margin_top(0)
        format_tab.pack_end(self.format_progressbar, False, False, 0)

        # Format status
        self.format_status = Gtk.Label(label="")
        format_tab.pack_end(self.format_status, False, False, 20)

        # Initial refresh
        logic.refresh_drives(self.drive_combo)
        logic.refresh_drives(self.format_drive_combo, self.format_drives_map)

        notebook.append_page(format_tab, Gtk.Label(label="Format USB"))

        # =====================================================
        # TAB 3: Verify Hash
        # =====================================================
        verify_tab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        verify_tab.set_border_width(15)

        # File selector
        file_label = Gtk.Label()
        file_label.set_markup("<b>Select a file:</b>")
        file_label.set_xalign(0)
        verify_tab.pack_start(file_label, False, False, 5)

        self.file_button = Gtk.FileChooserButton(
            title="Select File", action=Gtk.FileChooserAction.OPEN
        )
        self.file_button.set_margin_bottom(20)
        verify_tab.pack_start(self.file_button, False, False, 0)

        # User's hash
        hash_label = Gtk.Label()
        hash_label.set_markup("<b>Paste your hash here:</b>")
        hash_label.set_xalign(0)
        verify_tab.pack_start(hash_label, False, False, 5)

        self.hash_label_entry = Gtk.Entry()
        self.hash_label_entry.set_placeholder_text(
            "e.g. dc807b5de15fea2415d9d8f33ccd0ae4"
        )
        self.hash_label_entry.set_margin_bottom(20)
        verify_tab.pack_start(self.hash_label_entry, False, False, 0)

        # Algorithm selection
        algorithm_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        algorithm_column.set_halign(Gtk.Align.CENTER)

        algorithm_label = Gtk.Label()
        algorithm_label.set_markup("<b>Algorithm:</b>")
        algorithm_column.pack_start(algorithm_label, False, False, 0)

        self.verify_algorithm_combo = Gtk.ComboBoxText()
        for algo in ["MD5", "SHA-1", "SHA-256", "SHA-512"]:
            self.verify_algorithm_combo.append_text(algo)
        # Set default value to MD5
        self.verify_algorithm_combo.set_active(0)
        algorithm_column.pack_start(self.verify_algorithm_combo, False, False, 5)
        verify_tab.pack_start(algorithm_column, False, False, 0)

        # Connect signals
        self.file_button.connect("file-set", self.check_verify_ready)
        self.hash_label_entry.connect("changed", self.check_verify_ready)
        self.verify_algorithm_combo.connect("changed", self.check_verify_ready)

        # Verify button
        self.verify_button = Gtk.Button(label="Verify hash")
        self.verify_button.set_sensitive(False)
        self.verify_button.set_halign(Gtk.Align.CENTER)
        self.verify_button.set_margin_top(20)
        self.verify_button.connect("clicked", self.on_verify_clicked)
        verify_tab.pack_start(self.verify_button, False, False, 0)

        # Verify status
        self.verify_status = Gtk.Label(label="")
        self.verify_status.set_line_wrap(True)
        self.verify_status.set_halign(Gtk.Align.CENTER)
        self.verify_status.set_justify(Gtk.Justification.CENTER)
        verify_tab.pack_start(self.verify_status, False, False, 20)

        notebook.append_page(verify_tab, Gtk.Label(label="Verify hash"))

        # Footer area box
        footer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        footer_box.set_halign(Gtk.Align.CENTER)
        footer_box.set_margin_top(10)

        # About button
        about_button = Gtk.Button(label="About")
        about_button.set_relief(Gtk.ReliefStyle.NONE)  # flat look
        about_button.connect("clicked", self.on_about_clicked)
        footer_box.pack_start(about_button, False, False, 0)

        # Footer copyright line
        footer = Gtk.Label()
        footer.set_markup(
            "<span foreground='gray'><small>Copyright © 2025 santofrancesco</small></span>"
        )
        footer_box.pack_start(footer, False, False, 0)

        # Pack it at the very bottom
        vbox.pack_end(footer_box, False, False, 0)

    # =====================================================
    #  Handlers
    # =====================================================

    # Refreshes the list of drives in the Burn ISO tab
    def on_refresh_burn(self, button):
        logic.refresh_drives(self.drive_combo)
        self.check_burn_ready(None)

    # Enables "Write to USB" button if both ISO and drive are selected
    def check_burn_ready(self, widget):
        iso_path = self.iso_button.get_filename()
        drive_info = self.drive_combo.get_active_text()
        self.start_button.set_sensitive(logic.is_burn_ready(iso_path, drive_info))

    # Starts ISO writing process after confirmation
    def on_start_clicked(self, button):
        iso_path = self.iso_button.get_filename()
        drive_info = self.drive_combo.get_active_text()

        if not iso_path or not drive_info or "No USB" in drive_info:
            self.status.set_text("Please select an ISO and USB drive")
            return

        # Confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text="This will erase all data on the selected USB drive!",
        )
        details = Gtk.Label()
        details.set_use_markup(True)
        details.set_xalign(0)
        details.set_markup(
            f"<b>ISO file:</b>\n  <tt>{iso_path}</tt>\n\n"
            f"<b>USB drive:</b>\n  <tt>{drive_info}</tt>\n\n"
            f"Are you sure you want to continue?\n\n"
            f"<span foreground='red'><b>This action is irreversible!</b></span>"
        )
        details.set_margin_top(10)
        details.set_margin_bottom(10)
        details.set_margin_start(10)
        details.set_margin_end(10)
        box = dialog.get_content_area()
        box.add(details)
        details.show()

        response = dialog.run()
        dialog.destroy()

        if response != Gtk.ResponseType.OK:
            self.status.set_text("ISO writing cancelled")
            return

        # Continue if confirmed
        self.status.set_text("Writing ISO... please wait")

        # Run burning in a background thread so GTK stays responsive
        threading.Thread(
            target=logic.write_iso,
            args=(iso_path, drive_info, self.status, self.progressbar),
            daemon=True,
        ).start()

    # Updates label length limit and cluster size options when filesystem changes
    def on_fs_changed(self, combo):
        if not hasattr(self, "format_cluster_combo"):
            return  # Tab not built yet

        fs = combo.get_active_text()

        # Set label length rule
        max_len = 11 if fs == "FAT32" else 255
        self.format_label_entry.set_max_length(max_len)

        # Clear old cluster sizes
        self.format_cluster_combo.remove_all()

        # Populate cluster sizes per filesystem
        if fs == "FAT32":
            # 512 B – 64 KB
            sizes = ["512", "1024", "2048", "4096", "8192", "16384", "32768", "65536"]
        elif fs == "exFAT":
            # 512 B – 64 KB
            sizes = ["512", "1024", "2048", "4096", "8192", "16384", "32768", "65536"]
        elif fs == "NTFS":
            # 512 B – 64 KB
            sizes = ["512", "1024", "2048", "4096", "8192", "16384", "32768", "65536"]
        elif fs == "ext4":
            # Valid block sizes: 1 KB, 2 KB, 4 KB
            sizes = ["1024", "2048", "4096"]
        else:
            sizes = ["4096"]

        # Add them back to the combo
        for size in sizes:
            self.format_cluster_combo.append_text(size)

        # Reset width so it shrinks back when not exFAT
        self.format_cluster_combo.set_size_request(-1, -1)

        # Set default
        if "4096" in sizes:
            self.format_cluster_combo.set_active(sizes.index("4096"))
        else:
            self.format_cluster_combo.set_active(0)

    # Refreshes the list of drives in the Format tab
    def on_refresh_format(self, button):
        logic.refresh_drives(self.format_drive_combo, self.format_drives_map)
        self.check_format_ready(None)

    # Auto-fills label entry with vendor/model when a drive is selected
    def on_format_drive_selected(self, combo):
        idx = combo.get_active()
        if idx is None or idx not in self.format_drives_map:
            return
        drive = self.format_drives_map[idx]
        label = logic.get_vendor_model(drive["device"])
        self.format_label_entry.set_text(label)
        self.check_format_ready(None)

    # Enables "Format Drive" if drive, label, and cluster size are valid
    def check_format_ready(self, widget):
        drive_info = self.format_drive_combo.get_active_text()
        label = self.format_label_entry.get_text().strip()
        cluster = self.format_cluster_combo.get_active_text()
        ready = bool(drive_info and "No USB" not in drive_info and label and cluster)
        self.format_button.set_sensitive(ready)

    # Starts drive formatting process after confirmation
    def on_format_clicked(self, button):
        drive_info = self.format_drive_combo.get_active_text()
        label = self.format_label_entry.get_text().strip() or "UNTITLED"
        fs = self.format_fs_combo.get_active_text()
        cluster = self.format_cluster_combo.get_active_text()

        if not drive_info or "No USB" in drive_info:
            self.format_status.set_text("Please select a USB drive.")
            return

        # Confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text="This will erase all data on the selected drive! ⚠️",
        )
        dialog.format_secondary_text(
            f"Drive: {drive_info}\nFilesystem: {fs}\nNew label: {label}\n\nDo you want to continue?"
        )
        response = dialog.run()
        dialog.destroy()

        if response != Gtk.ResponseType.OK:
            self.format_status.set_text("Format cancelled.")
            return

        # Continue if confirmed
        self.format_status.set_text("Formatting drive...")

        self.format_progressbar.set_fraction(0.0)
        self.format_progressbar.set_show_text(False)
        self.format_progressbar.set_pulse_step(0.1)

        # Stop any old pulse loop if still running
        if hasattr(self.format_progressbar, "_pulse_id"):
            GLib.source_remove(self.format_progressbar._pulse_id)
            delattr(self.format_progressbar, "_pulse_id")

        # Start pulsing loop
        def pulse_bar():
            self.format_progressbar.pulse()
            return True  # keep repeating

        self.format_progressbar._pulse_id = GLib.timeout_add(100, pulse_bar)

        threading.Thread(
            target=logic.run_format,
            args=(
                drive_info,
                fs,
                label,
                cluster,
                self.format_status,
                self.format_progressbar,
            ),
            daemon=True,
        ).start()

    # Enables "Verify hash" if file, hash, and algorithm are provided
    def check_verify_ready(self, widget):
        file_path = self.file_button.get_filename()
        user_hash = self.hash_label_entry.get_text().strip()
        algo = self.verify_algorithm_combo.get_active_text()
        self.verify_button.set_sensitive(bool(file_path and user_hash and algo))

    # Starts hash verification in background thread
    def on_verify_clicked(self, button):
        file_path = self.file_button.get_filename()
        user_hash = self.hash_label_entry.get_text().strip().lower()
        algo = self.verify_algorithm_combo.get_active_text()
        self.verify_status.set_text("Verifying hash... please wait.")

        threading.Thread(
            target=logic.verify_hash,
            args=(file_path, algo, user_hash, self.verify_status),
            daemon=True,
        ).start()

    # Shows About dialog with app details
    def on_about_clicked(self, button):
        about = Gtk.AboutDialog(transient_for=self, modal=True)
        about.set_program_name("Tuxus")
        about.set_version("1.0.0")
        about.set_comments("ISO burning & USB formatting app for Linux.")
        about.set_license_type(Gtk.License.GPL_3_0)  # auto-fills GPLv3 text
        about.set_website("https://github.com/santofrancesco/tuxus")
        about.set_copyright("Copyright © 2025 santofrancesco")
        about.set_logo(Gtk.Image.new_from_file("icons/cd_fire.svg").get_pixbuf())
        about.run()
        about.destroy()

