#!/usr/bin/env python3

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
from gi.repository import Gtk

from gui import Tuxus

if __name__ == "__main__":
    win = Tuxus()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()

    print(
        """

┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  ooooooooooooo                                               │
│  8'   888   `8                                               │
│       888      oooo  oooo  oooo    ooo oooo  oooo   .oooo.o  │
│       888      `888  `888   `88b..8P'  `888  `888  d88(  "8  │
│       888       888   888     Y888'     888   888  `"Y88b.   │
│       888       888   888   .o8"'88b    888   888  o.  )88b  │
│      o888o      `V88V"V8P' o88'   888o  `V88V"V8P' 8""888P'  │
│                                                              │
│                    is currently running ...                  │
└──────────────────────────────────────────────────────────────┘
                     
                        Copyright © 2025 
"""
    )

    Gtk.main()
    print("Tuxus terminated successfully. Goodbye!")

