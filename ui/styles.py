MAIN_STYLE = """
/* SA-RP Linggo Professional Matte Slate Gray Theme */
QWidget#CentralWidget {
    background-color: rgba(27, 29, 34, 0.94);
    border: 1px solid rgba(60, 64, 75, 0.85);
    border-radius: 8px;
}

/* Header Frame */
QFrame#HeaderFrame {
    background-color: rgba(35, 38, 45, 0.95);
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    border-bottom: 1px solid rgba(55, 60, 70, 0.8);
    padding: 3px 6px;
}

QLabel#AppTitle {
    color: #F1F5F9;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.5px;
    font-family: 'Segoe UI', system-ui, sans-serif;
}

QLabel#StatusLabel {
    color: #10B981;
    font-size: 10px;
    font-weight: 600;
}

/* Header Buttons */
QPushButton.HeaderIconBtn {
    background-color: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 4px;
    padding: 3px;
    min-width: 24px;
    min-height: 24px;
    max-width: 24px;
    max-height: 24px;
}

QPushButton.HeaderIconBtn:hover {
    background-color: rgba(56, 189, 248, 0.15);
    border-color: #38BDF8;
}

QPushButton.HeaderIconBtn:pressed {
    background-color: rgba(56, 189, 248, 0.3);
}

QPushButton.HeaderIconBtn#CloseBtn:hover {
    background-color: rgba(239, 68, 68, 0.25);
    border-color: #EF4444;
}

QPushButton.HeaderIconBtn#LockBtn[locked="true"] {
    background-color: rgba(239, 68, 68, 0.2);
    border-color: #EF4444;
}

/* Scroll Area */
QScrollArea {
    background: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background: transparent;
}

/* Custom Slate Scrollbar */
QScrollBar:vertical {
    border: none;
    background: rgba(20, 22, 26, 0.5);
    width: 5px;
    margin: 0px;
    border-radius: 2px;
}

QScrollBar::handle:vertical {
    background: rgba(148, 163, 184, 0.35);
    min-height: 20px;
    border-radius: 2px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(56, 189, 248, 0.7);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Compact SAMP Chatlog Style Items */
QFrame.ChatItemCard {
    background-color: rgba(35, 38, 46, 0.65);
    border: 1px solid rgba(55, 60, 72, 0.5);
    border-radius: 4px;
    margin-bottom: 4px;
    padding: 5px 8px;
}

QFrame.ChatItemCard:hover {
    background-color: rgba(45, 49, 59, 0.85);
    border-color: rgba(70, 76, 90, 0.8);
}

QFrame.ChatItemCard[chat_type="SAYS"] {
    border-left: 3px solid #38BDF8;
}

QFrame.ChatItemCard[chat_type="ME"] {
    border-left: 3px solid #C084FC;
}

QFrame.ChatItemCard[chat_type="DO"] {
    border-left: 3px solid #A855F7;
}

QFrame.ChatItemCard[chat_type="OUTBOUND"] {
    border-left: 3px solid #06B6D4;
    background-color: rgba(6, 182, 212, 0.12);
}

QFrame.ChatItemCard[chat_type="OUTBOUND_VOICE"] {
    border-left: 3px solid #A855F7;
    background-color: rgba(168, 85, 247, 0.12);
}

QFrame.ChatItemCard[chat_type="ERROR"] {
    border-left: 3px solid #EF4444;
    background-color: rgba(239, 68, 68, 0.15);
}

QLabel.ChatTime {
    color: #64748B;
    font-size: 10px;
    font-family: 'Consolas', 'Segoe UI', monospace;
}

QLabel.OrigLine {
    color: #94A3B8;
    font-size: 11px;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QLabel.TransLine {
    font-size: 11px;
    font-weight: 600;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QLabel.TransLine[chat_type="SAYS"] {
    color: #38BDF8;
}

QLabel.TransLine[chat_type="ME"] {
    color: #E9D5FF;
}

QLabel.TransLine[chat_type="DO"] {
    color: #F0ABFC;
}

QLabel.TransLine[chat_type="OUTBOUND"] {
    color: #67E8F9;
}

QLabel.TransLine[chat_type="OUTBOUND_VOICE"] {
    color: #E9D5FF;
}

/* Settings Dialog Matte Slate Theme */
QDialog {
    background-color: #1A1C21;
    color: #F1F5F9;
    border: 1px solid #333742;
    border-radius: 8px;
}

QLineEdit, QComboBox, QSpinBox {
    background-color: #23262E;
    color: #F1F5F9;
    border: 1px solid #373C47;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border-color: #38BDF8;
}

QLabel {
    color: #CBD5E1;
    font-size: 12px;
}

/* SizeGrip Styling */
QSizeGrip {
    width: 12px;
    height: 12px;
    background: transparent;
}
"""
