# Built-in
import glob
import math
import os
import re
import sys

from Qt_py.Qt import QtWidgets, QtCore, QtGui

# =============================================================================
# GLOBALS
# =============================================================================
# Qt alignment
QT_ALIGN_CENTER = QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter
QT_ALIGN_LEFTTOP = QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop
QT_ALIGN_LEFTBTM = QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom
QT_ALIGN_LEFTCENTER = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
QT_ALIGN_RIGHTCENTER = QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter

# Qt color
R = 150
G = 150
B = 150
QT_BASE_COLOR = QtGui.QColor(R, G, B)
QT_DISABLE_COLOR = QtGui.QColor(R * .6, G * .6, B * .6)
QT_TEXT_COLOR = QtGui.QColor(0, 0, 0)
QT_DISABLE_TEXT_COLOR = QtGui.QColor(R * .7, G * .7, B * .7)
QT_NON_DEFAULT_TEXT_COLOR = QT_TEXT_COLOR
QT_BACKGROUND_COLOR = QtGui.QColor(R * .5, G * .5, B * .5)
QT_FOREGROUND_COLOR = QtGui.QColor(210, 210, 210)
QT_WARNING_COLOR = QtGui.QColor(220, 10, 10)

SUPPORTED_EXT = ['.exr', '.jpg', '.tex', '.png', '.tif', '.tiff', '.rat']


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

def get_sequence_regex(folder_path):
    """This generates a list of image regex.
    Frames are replaced with the wildcard for finding the same sequence pattern.
    """
    if not os.path.isdir(folder_path):
        raise OSError('[{}] does not exist.'.format(folder_path))

    seq_regex_set = set()
    image_list = os.listdir(folder_path)
    for image in image_list:
        if os.path.isfile(os.path.join(folder_path,image)) and os.path.splitext(image)[-1] in SUPPORTED_EXT:
            regex = re.compile('[0-9]+')
            replaced_filename = regex.sub('*', image)
            regex_filepath = os.path.join(folder_path, replaced_filename)
            seq_regex_set.add(regex_filepath)

    return list(seq_regex_set)

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
    def __init__(self, parent=None, **kwargs):
        super(ListWidget, self).__init__(parent=parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
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


class LineEdit(QtWidgets.QLineEdit, BaseWidget):
    value_changed = QtCore.Signal(object)

    def __init__(self, parent=None, **kwargs):
        """
        Customized line edit
        """
        self.default = kwargs.get('default', '')
        super(LineEdit, self).__init__(self.default, parent=parent)
        self.setAlignment(QT_ALIGN_LEFTCENTER)

        self.user_data = {}
        self._is_enable = True
        self.set_look()
        self.textChanged.connect(self.value_changed_cb)

        width = kwargs.get('width', 500)
        if width:
            if not kwargs.get('no_max_width', True):
                self.setMaximumWidth(int(width))
            self.setMinimumWidth(int(width))

        height = kwargs.get('height', 22)
        if height:
            self.setMaximumHeight(int(height))
            self.setMinimumHeight(int(height))

        self.set_value(self.default)

        self.bg_text_hint = str(kwargs.get('bg_text_hint', ''))
        if self.bg_text_hint:
            self.enable_bg_text_hint()
            self.set_bg_text_hint()

        validator = kwargs.get('validator')
        syntax = kwargs.get('syntax')
        if validator:
            self.set_validations(validator)
        elif syntax:
            self.set_validations(syntax=syntax)

    def enable_bg_text_hint(self):
        self.text = self.text_hint_text
        self.textChanged.connect(self.set_bg_text_hint)
        self.editingFinished.connect(self.set_bg_text_hint)
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self and event.type() == QtCore.QEvent.MouseButtonPress:
            if self.displayText() == self.bg_text_hint:
                is_blocked = self.blockSignals(True)
                self.set_value('')
                self.blockSignals(is_blocked)
        return False

    def set_bg_text_hint(self):
        if self.get_value() == '':
            is_blocked = self.blockSignals(True)
            self.set_value(self.bg_text_hint)
            self.blockSignals(is_blocked)
        self.update_pal()

    def text_hint_text(self):
        text = self.displayText()
        if text == self.bg_text_hint:
            return ''
        return str(text)

    def set_validations(self, validator_type='', syntax=''):
        """
        This method sets up all appropriate validations for text fields.
        If a character is invalid, it will not be allowed in the text field.
        """
        if not syntax:
            if validator_type == 'framerangevalidator':
                # 105-110x2 or 105-110:2
                syntax = "((\d+(,|\-\d+(,|x\d+,)))*)|((\d+\-\d+(:\d+)))*"
            elif validator_type == 'digitvalidator':
                syntax = "\d+"
            elif validator_type == 'digit1validator':
                syntax = "\d{1}"
            elif validator_type == 'digit2validator':
                syntax = "\d{2}"
            elif validator_type == 'digit4limitvalidator':
                syntax = "\d{4}"
            elif validator_type == 'digit5limitvalidator':
                syntax = "\d{5}"
            elif validator_type == 'digitcharvalidator':
                syntax = "\w{10}"
            elif validator_type == 'renderregionvalidator':
                syntax = "(\d{1,4},\d{1,4},\d{1,4},\d{1,4})"
            elif validator_type == 'descvalidator':
                syntax = "([a-zA-Z0-9][a-zA-Z0-9_]*_)?"
            else:
                syntax = ""

        if syntax:
            # None text
            syntax += "|()"
            if self.bg_text_hint:
                hint_syntax = "|({0})".format(self.bg_text_hint)
                syntax += hint_syntax

            validator = QtGui.QRegExpValidator(QtCore.QRegExp(syntax), self)

            if validator:
                self.setValidator(validator)

    def get_value(self):
        return str(self.text())

    def set_value(self, value):
        # Disable set_value
        if not self.is_enable:
            return
        self.setText(str(value))
        self.value_changed_cb(str(value))


class InputWidgetsFrame(QtWidgets.QFrame):
    value_changed = QtCore.Signal(object)
    """
    Base class of file input widgets grouping frame.
    This Qt frame contains several widgets, This is how we grouping
    widgets.
    """
    def __init__(self, parent=None):
        super(InputWidgetsFrame, self).__init__(parent)
        self.parent = parent
        self.build_widgets()

    @property
    def input_paths(self):
        input_folder = str(self.input_path_widget.get_value())
        input_paths = get_sequence_regex(input_folder)
        input_paths = [path.strip() for path in input_paths]
        return input_paths

    def build_widgets(self):
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setAlignment(QT_ALIGN_LEFTCENTER)

        # Input path pattern widget
        self.main_layout.addWidget(QtWidgets.QLabel("Input Folder:"))
        self.input_path_widget = LineEdit(parent=self)
        self.input_path_widget.value_changed.connect(self.input_changed_cb)
        self.main_layout.addWidget(self.input_path_widget)

        # File browser button
        file_dialog_button = QtWidgets.QPushButton('Browse')
        file_dialog_button.pressed.connect(self.open_file_dialog)
        self.main_layout.addWidget(file_dialog_button)

    def input_changed_cb(self):
        self.value_changed.emit(self.input_paths)

    def open_file_dialog(self):
        dir_path = os.path.expanduser('~')
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, 'Choose Input Path', dir_path)
        if folder_path:
            self.input_path_widget.set_value(str(folder_path))


class ImageListWidgetsFrame(QtWidgets.QFrame):
    """
    Class of image list widgets grouping frame.
    This Qt frame contains several widgets, This is how we grouping
    widgets.
    """
    def __init__(self, parent=None):
        super(ImageListWidgetsFrame, self).__init__(parent)
        self.parent = parent
        self.build_widgets()

    @property
    def file_paths(self):
        return self.file_list_widget.get_value()

    @property
    def preview_paths(self):
        return self.preview_list_widget.get_value()

    def build_widgets(self):
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setAlignment(QT_ALIGN_LEFTTOP)

        # File list widget
        l_side_layout = QtWidgets.QVBoxLayout()
        l_side_layout.setAlignment(QT_ALIGN_LEFTTOP)
        self.main_layout.addLayout(l_side_layout)
        self.file_list_widget = ListWidget(parent=self)
        l_side_layout.addWidget(QtWidgets.QLabel('Images to Convert:'))
        l_side_layout.addWidget(self.file_list_widget)

        # Preview result widget
        r_side_layout = QtWidgets.QVBoxLayout()
        r_side_layout.setAlignment(QT_ALIGN_LEFTBTM)
        self.main_layout.addLayout(r_side_layout)
        self.preview_list_widget = ListWidget(parent=self)
        r_side_layout.addWidget(QtWidgets.QLabel('Preview Result:'))
        r_side_layout.addWidget(self.preview_list_widget)


class RenumberWidget(QtWidgets.QDialog, BaseWidget):
    value_changed = QtCore.Signal(object)

    def __init__(self, *args, **kwargs):
        super(RenumberWidget, self).__init__()
        set_look(self.palette())
        self.sequence_regex = []
        self.build_widgets()

    @property
    def input_path(self):
        return self.control_frame.file_path

    def build_widgets(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setAlignment(QT_ALIGN_LEFTTOP)

        # Input folder widget
        self.input_frame = InputWidgetsFrame(parent=self)
        self.input_frame.value_changed.connect(self.input_changed_cb)
        self.main_layout.addWidget(self.input_frame)

        # Image list widget
        self.control_frame = ImageListWidgetsFrame(parent=self)
        self.main_layout.addWidget(self.control_frame)

        # Convert button
        self.convert_btn = QtWidgets.QPushButton('Do it!')
        self.convert_btn.pressed.connect(self.convert_pressed_cb)
        self.main_layout.addWidget(self.convert_btn)

        # Status
        self.status = QtWidgets.QLabel('Ready.', self)
        self.main_layout.addWidget(self.status)

    def convert_pressed_cb(self):
        self.status.setText('Starting re-numbering sequences...')
        self.rename_files()

    def preview_files(self, seq_regex_list):
        new_list = []

        for seq_pattern in seq_regex_list:
            same_seq_list = glob.glob(seq_pattern)
            same_seq_list.sort()

            # padding is based on the length of sequence. minimum is 2 digits.
            if int(math.log10(len(same_seq_list)) + 1) < 2:
                padding = '%02d'
            else:
                padding = '%0{}d'.format(int(math.log10(len(same_seq_list)) + 1))

            new_list.append(
                seq_pattern.replace('*', '[{0}-{1}]'.format(padding % 1, padding % (len(same_seq_list)))))

        return new_list

    def input_changed_cb(self, file_patterns):
        files = []
        for file_pattern in file_patterns:
            files.extend(
                filter(lambda x: os.path.splitext(x)[-1] in SUPPORTED_EXT,
                       glob.glob(file_pattern))
            )
        files = list(set(files))
        files.sort()
        self.control_frame.file_list_widget.set_value(files)

        new_image_list = self.preview_files(file_patterns)
        self.control_frame.preview_list_widget.set_value(new_image_list)

    def rename_files(self):
        seq_regex_list = self.input_frame.input_paths

        for seq_pattern in seq_regex_list:
            same_seq_list = glob.glob(seq_pattern)
            same_seq_list.sort()

            # padding is based on the length of sequence. minimum is 2 digits.
            if int(math.log10(len(same_seq_list)) + 1) < 2:
                padding = '%02d'
            else:
                padding = '%0{}d'.format(int(math.log10(len(same_seq_list)) + 1))

            for image in same_seq_list:
                frame_regex = re.compile('[0-9]+.')
                new_image_name = frame_regex.sub('{}.'.format(padding % (same_seq_list.index(image) + 1)), image)
                # print new_image_name
                os.rename(image, new_image_name)

        self.status.setText('Done re-numbering images!')


class RenumberDialog(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        super(RenumberDialog, self).__init__(*args, **kwargs)

        self.setWindowTitle('Re-number Image GUI')
        self.renumber_widget = RenumberWidget()
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(self.renumber_widget)