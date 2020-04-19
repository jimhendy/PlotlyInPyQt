import math
import os
import sys
import time

import numpy as np
import pandas as pd
import plotly
import plotly.graph_objects as go
from PyQt5 import Qt, QtCore, QtGui, QtWebEngineWidgets, QtWidgets

import qt_threads

# os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = '5050'
np.random.seed(123)


class Overlay(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        palette = QtGui.QPalette(self.palette())
        palette.setColor(palette.Background, QtCore.Qt.transparent)
        self.setPalette(palette)

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        # painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(event.rect(), QtGui.QBrush(QtGui.QColor(255, 255, 255, 127)))
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        n_ellipse = 6
        radius = 30
        size = 20
        for i in range(n_ellipse):
            if self.counter % n_ellipse == i:
                painter.setBrush(QtGui.QBrush(QtGui.QColor(127, 127, 255)))
            else:
                painter.setBrush(QtGui.QBrush(QtGui.QColor(127, 127, 127)))
            painter.drawEllipse(
                self.width() / 2 + radius * math.sin(2 * math.pi * i / n_ellipse),
                self.height() / 2 - radius * math.cos(2 * math.pi * i / n_ellipse),
                size,
                size,
            )
        painter.end()

    def showEvent(self, event):
        self.timer = self.startTimer(100)
        self.counter = 0

    def timerEvent(self, event):
        self.counter += 1
        self.update()
        if self.counter > 100:
            self.killTimer(self.timer)
            raise TimeoutError

    def stop(self):
        self.killTimer(self.timer)
        self.counter = 0
        self.hide()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):

        QtWidgets.QMainWindow.__init__(self, parent)

        widget = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(widget)

        top_bar = QtWidgets.QHBoxLayout()
        layout.addLayout(top_bar)

        self.threadpool = QtCore.QThreadPool()

        self.text_entry = QtWidgets.QLineEdit()
        self.text_entry.setPlaceholderText("Enter data bro!")
        top_bar.addWidget(self.text_entry)

        self.button = QtWidgets.QPushButton("Refresh")
        top_bar.addWidget(self.button)

        self.web = QtWebEngineWidgets.QWebEngineView()
        layout.addWidget(self.web)
        self.web_page = self.web.page()

        self.setCentralWidget(widget)

        self.overlay = Overlay(self.centralWidget())
        self.overlay.hide()

        self.button.clicked.connect(self.overlay.show)
        self.button.clicked.connect(self.update_data_trigger)

    def resizeEvent(self, event):
        self.overlay.resize(event.size())
        event.accept()

    def update_data_trigger(self):
        def update_data(progress_callback):
            n_days = 1000
            n_stocks = int(self.text_entry.text())

            df = (
                pd.DataFrame(
                    np.random.normal(0, 0.01, (n_days, n_stocks)),
                    index=pd.date_range("2000-01-01", freq="b", periods=n_days),
                )
                .add(1)
                .cumprod()
            )

            fig = go.Figure(
                data=[go.Scattergl(x=df.index, y=df[c].values) for c in df.columns],
                layout={
                    "title": "Test Plot", 
                    "template": "ggplot2",
                    "margin": {'t':25, 'l':0, 'b':0, 'r':0},
                    'yaxis': {'automargin': True, 'title':'Data Stuff ($)'},
                    'xaxis': {'automargin': True},
                },
            )

            # create the initial html code
            html = f"""
            <html>
            <head>
                <meta charset="utf-8" />
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            </head>
            <body>
            {fig.to_html(include_plotlyjs=False, full_html=False)}
            </body>
            </html>"""
            self.web_page.runJavaScript(
                f'document.body.innerHTML = null; document.write(`{html}`);'
            )
            del fig
            del df

        worker = qt_threads.Worker(update_data)
        worker.signals.finished.connect(self.overlay.stop)
        self.threadpool.start(worker)


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
