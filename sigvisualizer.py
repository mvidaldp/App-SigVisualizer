import colorsys as cs
import json
import sys

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QBrush, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QStatusBar, QTreeWidgetItem

from ui_sigvisualizer import Ui_MainWindow


class SigVisualizer(QMainWindow):
    stream_expanded = pyqtSignal(str, list, list)

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Real Time Signal Visualizer")
        self.ui.treeWidget.setHeaderLabel("Streams")
        self.setWindowIcon(QIcon("sigvisualizer.ico"))

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        self.ui.toggleButton.setIcon(QIcon("icons/chevron_left.svg"))
        self.ui.toggleButton.setIconSize(QSize(30, 30))

        self.ui.toggleButton.clicked.connect(self.toggle_panel)
        self.ui.updateButton.clicked.connect(self.ui.widget.dataTr.update_streams)
        self.ui.widget.dataTr.updateStreamNames.connect(self.update_metadata_widget)
        self.panelHidden = False

        self.ui.treeWidget.itemExpanded.connect(self.tree_item_expanded)
        self.stream_expanded.connect(self.ui.widget.dataTr.handle_stream_expanded)
        self.channels_mapping = self.load_channels("EEG_channels.json")
        self.ui.treeWidget.itemChanged.connect(self.update_changed)
        self.ui.treeWidget.itemClicked.connect(self.toggle_checks)
        self.checked_changed = False
        self.stream_name = None
        self.checked = []
        self.colors = []

    def generate_colors(self, n_ch):
        HSV = [(x * 1.0 / n_ch, 0.75, 0.92) for x in range(n_ch)]
        RGB = [list(map(lambda x: int(x * 255), cs.hsv_to_rgb(*hsv))) for hsv in HSV]
        return RGB

    def recolor_checks(self, parent):
        color_idx = 0

        for i in range(parent.childCount()):
            if i in self.checked:
                r, g, b = self.colors[color_idx]
                parent.child(i).setForeground(0, QBrush(QColor(r, g, b)))
                color_idx += 1
            else:
                parent.child(i).setForeground(0, QBrush(Qt.black))

    def update_checks(self, it):
        its = it.childCount()
        if its == 0:
            it = it.parent()
            its = it.childCount()
        state = Qt.Checked
        checked = [i for i in range(its) if it.child(i).checkState(0) == state]
        if self.checked != checked:
            self.checked = checked
            self.colors = self.generate_colors(len(self.checked))
            self.stream_expanded.emit(self.stream_name, self.checked, self.colors)
            self.recolor_checks(it)

    def update_changed(self, item):
        self.checked_changed = True

    def toggle_checks(self, item):
        if self.checked_changed:
            children = item.childCount()
            if children > 0:
                if not self.stream_name:
                    self.stream_name = item.text(0)
                toggle = item.checkState(0)
                for i in range(children):
                    item.child(i).setCheckState(0, toggle)
            self.update_checks(item)
        self.checked_changed = False

    def load_channels(self, filename):
        file = open(filename, "r")
        eeg_channels = json.load(file)  # load file content as dict
        file.close()
        return eeg_channels

    def tree_item_expanded(self, widget_item):
        self.stream_name = widget_item.text(0)
        for it_ix in range(self.ui.treeWidget.topLevelItemCount()):
            item = self.ui.treeWidget.topLevelItem(it_ix)
            if item.text(0) != self.stream_name:
                item.setExpanded(False)
        self.stream_expanded.emit(self.stream_name, self.checked, self.colors)

    def update_metadata_widget(self, metadata, default_idx):
        for s_ix, s_meta in enumerate(metadata):
            item = QTreeWidgetItem(self.ui.treeWidget)
            item.setText(0, s_meta["name"])
            item.setCheckState(0, Qt.Checked)
            mapping = self.channels_mapping
            ch_cnt = s_meta["ch_count"]
            self.colors = self.generate_colors(ch_cnt)
            for m in range(ch_cnt):
                channel_item = QTreeWidgetItem(item)
                label = f"ch-{m+1}"
                ch = m + 1 if m + 1 >= 10 else f"0{m + 1}"
                ch_label = f":  {mapping[label]}" if label in mapping else ""
                channel_item.setText(0, f"Ch-{ch}{ch_label}")
                r, g, b = self.colors[m]
                channel_item.setForeground(0, QBrush(QColor(r, g, b)))
                channel_item.setCheckState(0, Qt.Checked)
                self.checked.append(m)

            expanded = True if s_ix == default_idx else False
            item.setExpanded(expanded)
            self.ui.treeWidget.addTopLevelItem(item)

        self.ui.treeWidget.setAnimated(True)
        self.statusBar.showMessage(
            "Sampling rate: {}Hz".format(metadata[default_idx]["srate"])
        )

    def toggle_panel(self):
        if self.panelHidden:
            self.panelHidden = False
            self.ui.treeWidget.show()
            self.ui.updateButton.show()
            self.ui.toggleButton.setIcon(QIcon("icons/chevron_left.svg"))
            self.ui.toggleButton.setIconSize(QSize(30, 30))
        else:
            self.panelHidden = True
            self.ui.treeWidget.hide()
            self.ui.updateButton.hide()
            self.ui.toggleButton.setIcon(QIcon("icons/chevron_right.svg"))
            self.ui.toggleButton.setIconSize(QSize(30, 30))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SigVisualizer()
    window.show()
    sys.exit(app.exec_())
