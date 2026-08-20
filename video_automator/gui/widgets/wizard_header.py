"""Visual step indicator widget for the wizard."""
from typing import List
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush


STEPS = [
    "Video",
    "Audio",
    "Subtitles",
    "Translation",
    "Duration",
    "Output",
    "Naming",
    "Review",
    "Process",
    "Done",
]


class StepDot(QWidget):
    """A single step in the indicator — circle + label."""

    def __init__(self, number: int, label: str, state: str = "inactive", parent=None):
        super().__init__(parent)
        self.number = number
        self.label = label
        self.state = state  # 'inactive' | 'active' | 'completed'
        self.setFixedSize(52, 52)

    def set_state(self, state: str):
        self.state = state
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, 18
        r = 14

        if self.state == "active":
            fill = QColor("#7c3aed")
            border = QColor("#a78bfa")
            text_color = QColor("#ffffff")
            label_color = QColor("#c4b5fd")
        elif self.state == "completed":
            fill = QColor("#059669")
            border = QColor("#34d399")
            text_color = QColor("#ffffff")
            label_color = QColor("#6ee7b7")
        else:
            fill = QColor("#1a1a27")
            border = QColor("#374151")
            text_color = QColor("#6b7280")
            label_color = QColor("#4b5563")

        # Draw circle
        painter.setPen(QPen(border, 2))
        painter.setBrush(QBrush(fill))
        painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        # Draw number or checkmark
        painter.setPen(text_color)
        font = QFont("Segoe UI", 8, QFont.Weight.Bold)
        painter.setFont(font)
        if self.state == "completed":
            painter.drawText(cx - r, cy - r, r * 2, r * 2, Qt.AlignmentFlag.AlignCenter, "✓")
        else:
            painter.drawText(cx - r, cy - r, r * 2, r * 2, Qt.AlignmentFlag.AlignCenter, str(self.number))

        # Draw label below circle
        painter.setPen(label_color)
        font2 = QFont("Segoe UI", 7)
        painter.setFont(font2)
        painter.drawText(0, cy + r + 2, w, 16, Qt.AlignmentFlag.AlignCenter, self.label)


class ConnectorLine(QWidget):
    """Horizontal connector line between step dots."""
    def __init__(self, completed: bool = False, parent=None):
        super().__init__(parent)
        self.completed = completed
        self.setFixedSize(28, 52)

    def set_completed(self, completed: bool):
        self.completed = completed
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor("#7c3aed") if self.completed else QColor("#252535")
        painter.setPen(QPen(color, 2, Qt.PenStyle.SolidLine))
        mid = self.height() // 2 - 2
        painter.drawLine(0, mid, self.width(), mid)


class WizardHeader(QWidget):
    """Step indicator bar for the top of the wizard."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("wizard_header")
        self.setFixedHeight(68)

        self._dots: List[StepDot] = []
        self._connectors: List[ConnectorLine] = []
        self._current_step = 0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setSpacing(0)

        layout.addStretch()

        for i, step_name in enumerate(STEPS):
            dot = StepDot(i + 1, step_name, "inactive" if i > 0 else "active")
            self._dots.append(dot)
            layout.addWidget(dot)

            if i < len(STEPS) - 1:
                conn = ConnectorLine(False)
                self._connectors.append(conn)
                layout.addWidget(conn)

        layout.addStretch()

    def set_step(self, step: int):
        """
        Set the currently active step (0-indexed).
        Steps before current are marked completed.
        """
        self._current_step = step
        for i, dot in enumerate(self._dots):
            if i < step:
                dot.set_state("completed")
            elif i == step:
                dot.set_state("active")
            else:
                dot.set_state("inactive")
        for i, conn in enumerate(self._connectors):
            conn.set_completed(i < step)
