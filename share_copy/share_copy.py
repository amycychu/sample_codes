# Built-in
import os
import hou
import time
import math

#from Qt_py.Qt import QtCore, QtGui, QtWidgets
try:
    from PySide2 import QtCore, QtGui, QtWidgets
except:
    from PySide import QtGui, QtCore

try:
   import hou
   IN_HOU = True
except ImportError:
   IN_HOU = False

# =============================================================================
# GLOBALS
# =============================================================================
# Qt alignment
QT_ALIGN_CENTER = QtCore.Qt.AlignVCenter|QtCore.Qt.AlignHCenter
QT_ALIGN_LEFTTOP = QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop
QT_ALIGN_LEFTBTM = QtCore.Qt.AlignLeft|QtCore.Qt.AlignBottom
QT_ALIGN_LEFTCENTER = QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter
QT_ALIGN_RIGHTCENTER = QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter

# Qt color
R = 150
G = 150
B = 150
QT_BASE_COLOR = QtGui.QColor(R, G, B)
QT_DISABLE_COLOR = QtGui.QColor(R*.6, G*.6, B*.6)
QT_TEXT_COLOR = QtGui.QColor(0, 0, 0)
QT_DISABLE_TEXT_COLOR = QtGui.QColor(R*.7, G*.7, B*.7)
QT_NON_DEFAULT_TEXT_COLOR = QT_TEXT_COLOR#QtGui.QColor(225, 225, 225)
QT_BACKGROUND_COLOR = QtGui.QColor(R*.5, G*.5, B*.5)
QT_FOREGROUND_COLOR = QtGui.QColor(210, 210, 210)
QT_WARNING_COLOR = QtGui.QColor(220, 10, 10)

SHARE_DIR = "/var/tmp/houdini/share/"
#SHARE_DIR = "F:/coding/test/"

CATEGORIES = ("Object", "Sop", "Shop", "ChopNet", "Chop", "CopNet", "Cop2", "VopNet", "Vop", "Driver")
COMMON_NAMES = ("Obj", "Sop", "Shop", "ChopNet", "Chop", "CopNet", "Cop", "VopNet", "Vop", "Rop")

CATEGORY_TRANSLATE = {
   "Object": "Obj",
   "Driver": "Rop",
   "Cop2": "Cop"
}

# =============================================================================
# FUNCTIONS
# =============================================================================
def set_look(pal):
    pal.setColor(QtGui.QPalette.Base, QT_BASE_COLOR)
    pal.setColor(QtGui.QPalette.Text, QT_TEXT_COLOR)
    pal.setColor(QtGui.QPalette.Window, QT_BACKGROUND_COLOR)
    pal.setColor(QtGui.QPalette.WindowText, QT_FOREGROUND_COLOR)
    pal.setColor(QtGui.QPalette.WindowText, QT_TEXT_COLOR)
    pal.setColor(QtGui.QPalette.Button, QT_BASE_COLOR)
    pal.setColor(QtGui.QPalette.ButtonText, QT_TEXT_COLOR)
    return pal

def parent_hou(widget):
    if IN_HOU and hou.isUIAvailable():
        widget.setParent(hou.ui.mainQtWindow(), QtCore.Qt.Window)

def share_copy():
    """
    Get the selected nodes and network items and save them as cpio file to 
    the share directory
    """
    items = hou.selectedItems(True)

    if len(items) > 0:
        first_node = None

        for i in items:
            if i.networkItemType() == hou.networkItemType.Node:
                first_node = i
        if first_node:
            node_category_type = first_node.type().category().name()
            file_name = "{0}/{1}_{2}.cpio".format(SHARE_DIR, os.getenv("USER"), node_category_type)
            first_node.parent().saveItemsToFile(items, file_name, save_hda_fallbacks=True)
    else:
        message = "Please select node(s)."
        hou.ui.displayMessage(message)

# =============================================================================
# CLASSES
# =============================================================================
class BaseWidget(object):
    """
    Base widget class. This class provides simple functionality like,
    default/non-default colorized visual helper, enable/disable functionality.
    """
    @property
    def is_enable(self):
        return self._is_enable

    @is_enable.setter
    def is_enable(self, value):
        self._is_enable = value
        self._set_enable(value)

    def _set_enable(self, value):
        self.update_pal()
        self.setEnabled(value)

    def update_pal(self):
        if not self.is_enable:
            self.setPalette(self.disable_pal)
        else:
            if self.get_value() == self.default:
                self.setPalette(self.pal)
            else:
                self.setPalette(self.non_default_pal)

    def set_look(self):
        """
        Set custom look. Including regular look, disable look, and
        non default look
        """
        self.pal = set_look(self.palette())
        self.setPalette(self.pal)

        self.disable_pal = self.palette()
        self.disable_pal.setColor(QtGui.QPalette.Base, QT_DISABLE_COLOR)
        self.disable_pal.setColor(QtGui.QPalette.Text, QT_DISABLE_TEXT_COLOR)

        self.non_default_pal = self.palette()
        self.non_default_pal.setColor(QtGui.QPalette.Base, QT_BASE_COLOR)
        self.non_default_pal.setColor(QtGui.QPalette.Text,
                                      QT_NON_DEFAULT_TEXT_COLOR)

        self.hint_pal = self.palette()
        self.hint_pal.setColor(QtGui.QPalette.Base, QT_BASE_COLOR)
        self.hint_pal.setColor(QtGui.QPalette.Text, QT_DISABLE_TEXT_COLOR)

    def value_changed_cb(self, value):
        self.update_pal()
        self.value_changed.emit(self.get_value())


class ListWidget(QtWidgets.QListWidget, BaseWidget):
    value_changed = QtCore.Signal(object)
    def __init__(self, parent=None, **kwargs):
        super(ListWidget, self).__init__(parent=parent)
        self._is_enable = True
        self.set_look()

    def set_value(self, value):
        # Disable set_value
        if not self.is_enable:
            return

        if isinstance(value, (str, tuple)):
            value = list(value)

        if not isinstance(value, list):
            return

        self.clear()
        self.addItems(filter(lambda x: isinstance(x, str), value))

    def get_value(self):
        value = []
        for item in self.selectedItems():
            value.append(str(item.text()))

        return value


class SharePasteWidget(QtWidgets.QDialog, BaseWidget):
    cancel_pressed = QtCore.Signal(object)
    def __init__(self, *args, **kwargs):
        super(SharePasteWidget, self).__init__()
        set_look(self.palette())
        self.destination = self.get_destination()
        self.remap = {}
        self.build_widgets()

    @property
    def selected_item(self):
        return self.share_list_widget.get_value()

    def build_widgets(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setAlignment(QT_ALIGN_CENTER)

        layout = QtWidgets.QVBoxLayout()
        self.main_layout.addLayout(layout)
        # Share items list widget
        self.share_list_widget = ListWidget(parent=self)
        items = self.get_share_files()
        self.share_list_widget.set_value(items)
        layout.addWidget(QtWidgets.QLabel('Snippets to paste:'))
        layout.addWidget(self.share_list_widget)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.main_layout.addLayout(button_layout)
        self.paste_btn = QtWidgets.QPushButton('Paste!')
        self.paste_btn.pressed.connect(self.do_paste)
        button_layout.addWidget(self.paste_btn)
        self.cancel_btn = QtWidgets.QPushButton('Cancel')
        self.cancel_btn.pressed.connect(self.cancel_pressed_cb)
        button_layout.addWidget(self.cancel_btn)

    def get_destination(self):
        """
        Get user's current pane as the paste destination
        """
        pane_list = hou.ui.currentPaneTabs()

        for p in range(0, len(pane_list)):
            if pane_list[p].type() == hou.paneTabType.NetworkEditor and pane_list[p].isCurrentTab():
                destination = pane_list[p].pwd()
                return destination

    def get_share_files(self):
        """
        Get the same category (destination) file list and sort them based on
        modified time from nearest to furthest.
        """
        paste_category_type = self.destination.childTypeCategory().name()
        now = time.time()

        dir_list = os.listdir(SHARE_DIR)
        new_list = []

        for i in range(0, len(dir_list)):
            # get the file's last modified time and calculate the age
            mod_time = os.path.getmtime(SHARE_DIR + dir_list[i])
            age = now - mod_time
            entry = {"item": dir_list[i], "age": age}
            new_list.append(entry)
        new_list.sort(key=lambda entry: entry["age"])

        paste_list = []
        for i in range(0, len(new_list)):
            (username, cat) = new_list[i]["item"].split(".")[0].split("_")
            if cat == paste_category_type:
                if cat in CATEGORY_TRANSLATE:
                    cat = CATEGORY_TRANSLATE[cat]

                formatted_age = self.format_age(new_list[i]["age"])
                name = "{0}: {1} ({2})".format(username, cat, formatted_age)
                paste_list.append(name)
                self.remap[name] = new_list[i]["item"]

        return paste_list

    def format_age(self, age):
        """
        Reformat age in readable seconds, minutes, hrs, and days.
        :param age: in seconds
        """
        if age < 90:
            return "%d seconds" % (age)

        if age < 60*60*2:
            return "%d minutes" % (age/60)

        if age < 60*60*48:
            return "%0.1f hours" % (math.floor(10*age/(60*60))/10)

        return "%0.2f days" % (math.floor(100*age/(60*60*24))/100)

    def do_paste(self):
        """
        Load the selected cpio file to the destination category
        """
        name = self.remap.get(self.selected_item[0])
        file_path = "{0}/{1}".format(SHARE_DIR, name)
        current_dir = hou.pwd().path()
        hou.cd(self.destination.path())
        hou.hscript("opread {}".format(file_path))
        hou.cd(current_dir)

    def cancel_pressed_cb(self):
        self.cancel_pressed.emit(True)


class SharePasteDialog(QtWidgets.QDialog):
    cancel_pressed = QtCore.Signal(object)
    def __init__(self, *args, **kwargs):
        super(SharePasteDialog, self).__init__(*args, **kwargs)
        # Parent to Houdini
        if IN_HOU and not 'parent' in kwargs:
            parent_hou(self)

        self.setWindowTitle('Share Paste GUI')
        self.share_paste_widget = SharePasteWidget()
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(self.share_paste_widget)

        self.share_paste_widget.cancel_pressed.connect(self.close)