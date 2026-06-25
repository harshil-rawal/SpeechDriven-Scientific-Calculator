import sys
import re
import speech_recognition as sr
import threading
import pyttsx3

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QListWidget,
    QHBoxLayout,
    QMessageBox
)

from PyQt6.QtGui import QFont, QKeyEvent
from PyQt6.QtCore import Qt, QTimer
from typing import cast
from PyQt6.QtGui import QKeyEvent
from num2words import num2words


from sympy import (
    sympify,
    N,
    
)


class Calculator(QWidget):
                
    def __init__(self):
        super().__init__()
        # self.engine = pyttsx3.init()
        
        self.last_answer = "0"
        self.setWindowTitle("Voice Calci")
        self.setFixedSize(920, 720)

        self.initUI()
        self.voice_enabled = True
        
        self.mic_frames = ["🎤", "🎙️", "🔴", "🎙️"]
        self.mic_index = 0

        self.mic_timer = QTimer()
        self.mic_timer.timeout.connect(self.animate_mic)

    def initUI(self):

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(22)

        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        left_layout.setSpacing(14)
        right_layout.setSpacing(12)

        self.expression = QLineEdit()
        self.expression.setObjectName("expression")
        self.expression.setReadOnly(True)
        self.expression.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.expression.setFont(QFont("Segoe UI", 18))
        self.expression.setMinimumHeight(64)

        self.answer = QLabel("0")
        self.answer.setObjectName("answer")
        self.answer.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.answer.setFont(QFont("Segoe UI Semibold", 42))
        self.answer.setMinimumHeight(76)

        left_layout.addWidget(self.expression)
        left_layout.addWidget(self.answer)
        
        history_label = QLabel("History")
        history_label.setObjectName("historyLabel")
        history_label.setFont(QFont("Segoe UI Semibold", 16))

        self.history = QListWidget()
        self.history.setObjectName("history")
        self.history.setFont(QFont("Segoe UI", 12))
        self.load_history()
        self.clear_history_btn = QPushButton("Clear History")
        self.clear_history_btn.setObjectName("clearHistory")
        self.clear_history_btn.setMinimumHeight(46)

        right_layout.addWidget(history_label)
        right_layout.addWidget(self.history)
        right_layout.addWidget(self.clear_history_btn)
        
        self.clear_history_btn.clicked.connect(self.clear_history)
        self.history.itemDoubleClicked.connect(self.use_history)
        grid = QGridLayout()
        grid.setSpacing(10)

        buttons = [
            ["sin", "cos", "tan", "√"],
            ["log", "ln", "π", "e"],
            ["!", "%", "^", "⌫"],
            ["7", "8", "9", "÷"],
            ["4", "5", "6", "×"],
            ["1", "2", "3", "-"],
            ["0", ".", "=", "+", "ℹ️"],
            ["Ans", "(", ")", "C", "🎤", "🔊"]
        ]

        for row, button_row in enumerate(buttons):
            for col, text in enumerate(button_row):
                btn = QPushButton(text)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                if text == "🎤":
                    self.mic_button = btn
                if text in ["+", "-", "×", "÷", "="]:
                    btn.setStyleSheet("""
                    QPushButton{
                        background-color: #8f6d2b;
                        color: white;
                        border-radius: 15px;
                        font-size: 18px;
                    }

                    QPushButton:hover{
                     background-color: #a27d35;
                    }
                     """)
                    
                # Scientific buttons
                elif text in ["sin", "cos", "tan", "log", "ln",
                            "√", "π", "e", "!", "%", "^", "⌫"]:
                    btn.setStyleSheet("""
                        QPushButton{
                            background-color: #8a8f96;
                            color: black;
                            border-radius: 15px;
                            font-size: 16px;
                        }

                        QPushButton:hover{
                            background-color: #9ba0a7;
                        }
                    """)
                    
                btn.setStyleSheet("")

                if text in ["+", "-", "Ã—", "Ã·", "="]:
                    btn.setProperty("role", "operator")
                elif text in ["C", "Ans", "(", ")"]:
                    btn.setProperty("role", "control")
                elif text in ["ðŸŽ¤", "ðŸ”Š", "â„¹ï¸"]:
                    btn.setProperty("role", "voice")
                elif text.replace(".", "", 1).isdigit():
                    btn.setProperty("role", "number")
                else:
                    btn.setProperty("role", "function")

                if text in ["+", "-", "="] or (row in [3, 4] and col == 3):
                    btn.setProperty("role", "operator")
                elif (row == 6 and col == 4) or (row == 7 and col in [4, 5]):
                    btn.setProperty("role", "voice")

                btn.setMinimumSize(88, 62)
                btn.setFont(QFont("Segoe UI Semibold", 14))

                btn.clicked.connect(self.button_clicked)

                grid.addWidget(btn, row, col)

        left_layout.addLayout(grid)
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 1)

        self.setLayout(main_layout)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()
        self.setStyleSheet("""
QWidget{
    background-color: #0f1115;
    color: #f5f7fb;
    font-family: "Segoe UI";
}

QLineEdit{
    background-color: #171a21;
    border: 1px solid #2b303a;
    border-radius: 18px;
    color: #aeb6c4;
    padding: 14px 18px;
    selection-background-color: #ff9f0a;
}

QLineEdit#expression{
    font-size: 18px;
}

QLabel#answer{
    background-color: #171a21;
    border: 1px solid #2b303a;
    border-radius: 22px;
    color: #ffffff;
    padding: 4px 20px 12px 20px;
}

QLabel#historyLabel{
    color: #d7dce5;
    padding: 4px 2px;
}

QPushButton{
    background-color: #2d323c;
    border: 0;
    border-radius: 28px;
    color: #f8fafc;
    font-size: 16px;
    padding: 8px;
}

QPushButton:hover{
    background-color: #3a414d;
}

QPushButton:pressed{
    background-color: #4b5565;
    padding-top: 10px;
}

QPushButton[role="number"]{
    background-color: #333943;
}

QPushButton[role="function"]{
    background-color: #707784;
    color: #101217;
}

QPushButton[role="function"]:hover{
    background-color: #858d9a;
}

QPushButton[role="control"]{
    background-color: #4a505b;
    color: #ffffff;
}

QPushButton[role="control"]:hover{
    background-color: #5b6270;
}

QPushButton[role="operator"]{
    background-color: #ff9f0a;
    color: #ffffff;
    font-size: 20px;
}

QPushButton[role="operator"]:hover{
    background-color: #ffb13b;
}

QPushButton[role="voice"]{
    background-color: #1f6feb;
    color: #ffffff;
}

QPushButton[role="voice"]:hover{
    background-color: #2f81f7;
}

QListWidget{
    background-color: #171a21;
    border: 1px solid #2b303a;
    border-radius: 18px;
    color: #d7dce5;
    padding: 10px;
}

QListWidget::item{
    border-radius: 10px;
    padding: 8px 10px;
    margin: 2px 0;
}

QListWidget::item:selected{
    background-color: #263247;
    color: #ffffff;
}

QPushButton#clearHistory{
    background-color: #232832;
    border-radius: 16px;
    color: #d7dce5;
    font-size: 13px;
}

QPushButton#clearHistory:hover{
    background-color: #303744;
}
""")

    def button_clicked(self):

        button = self.sender()

        if not isinstance(button, QPushButton):
            return

        text = button.text()
        current = self.expression.text()

        if text == "C":
            self.expression.clear()
            self.answer.setText("0")

        elif text == "⌫":
            self.expression.setText(current[:-1])

        elif text == "=":
            self.calculate()
            
        elif text == "Ans":
            self.expression.setText(current + self.last_answer)
            
        elif text == "sin":
            self.expression.setText(current + "sin(")

        elif text == "cos":
            self.expression.setText(current + "cos(")

        elif text == "tan":
            self.expression.setText(current + "tan(")

        elif text == "√":
            self.expression.setText(current + "sqrt(")

        elif text == "log":
            self.expression.setText(current + "log(")

        elif text == "ln":
            self.expression.setText(current + "ln(")

        elif text == "π":
            self.expression.setText(current + "pi")

        elif text == "e":
            self.expression.setText(current + "E")
            
        elif text == "ℹ️":
            self.show_help()
                        
        elif text == "🎤":
            threading.Thread(target=self.listen_voice, daemon=True).start()                
        
        elif text == "🔊":

            self.voice_enabled = not self.voice_enabled

            if self.voice_enabled:
                self.answer.setText("Voice ON")
            else:
                self.answer.setText("Voice OFF")

        else:
            self.expression.setText(current + text)
            
    def keyPressEvent(self, a0):
        event = cast(QKeyEvent, a0)

        key = event.key()
        current = self.expression.text()

        # Enter / Return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.calculate()

        # Backspace
        elif key == Qt.Key.Key_Backspace:
            self.expression.setText(current[:-1])

        # Escape
        elif key == Qt.Key.Key_Escape:
            self.expression.clear()
            self.answer.setText("0")

        else:
            text = event.text()

            allowed = "0123456789.+-*/()%^"

            if text in allowed:
                self.expression.setText(current + text)
                
    def calculate(self):
        try:
            current = self.expression.text()

            expr = current

            expr = expr.replace("^", "**")
            expr = expr.replace("%", "/100")
            expr = expr.replace("×", "*")
            expr = expr.replace("÷", "/")

            # ln(x)
            expr = re.sub(
                r'ln\((.*?)\)',
                r'log(\1)',
                expr
            )

            # log(x)
            expr = re.sub(
                r'log\((.*?)\)',
                r'log(\1,10)',
                expr
            )

            # Degree mode
            expr = re.sub(
                r'sin\((.*?)\)',
                lambda m: f'sin(pi*({m.group(1)})/180)',
                expr
            )

            expr = re.sub(
                r'cos\((.*?)\)',
                lambda m: f'cos(pi*({m.group(1)})/180)',
                expr
            )

            expr = re.sub(
                r'tan\((.*?)\)',
                lambda m: f'tan(pi*({m.group(1)})/180)',
                expr
            )

            result = float(N(sympify(expr)))
            
            answer = f"{result:.6f}".rstrip("0").rstrip(".")
            
            self.answer.setText(answer)
            self.last_answer = answer
            
            
            if self.voice_enabled:
                
                self.speak_answer(answer)

            history_entry = f"{current} = {answer}"
            self.history.addItem(history_entry)
            self.save_history(history_entry)

        except Exception as e:
            print(e)
            self.answer.setText("Error")
            
    def listen_voice(self):
   
        recognizer = sr.Recognizer()

        try:
            self.mic_index = 0
            self.mic_timer.start(300)
            self.answer.setText("🎤 Listening...")
            self.mic_button.setText("🔴")

            with sr.Microphone() as source:

                recognizer.adjust_for_ambient_noise(
                    source,
                    duration=0.5
                )

                audio = recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=5
                )

            command = recognizer.recognize_google(audio) #pyright: ignore

            print(command)

            expression = command.lower()

            expression = expression.replace("double the answer",f"{self.last_answer} * 2")
            expression = expression.replace("half of the answer",f"{self.last_answer} / 2")
            expression = expression.replace("square the answer",f"{self.last_answer} ^ 2")
            expression = expression.replace("previous answer",self.last_answer)
            expression = expression.replace("last answer",self.last_answer)
            expression = expression.replace("the answer",self.last_answer)
            expression = expression.replace("answer",self.last_answer)
            expression = expression.replace("ans", self.last_answer)
            

            expression = expression.replace("what is", "")
            expression = expression.replace("calculate", "")
            expression = expression.replace("find", "")

            expression = expression.replace("degrees", "")
            expression = expression.replace("degree", "")

            expression = expression.replace("the", "")
            expression = expression.strip()
            expression = expression.replace(" x ", " × ")
            expression = expression.replace(" X ", " × ")
            expression = expression.replace(" route ", " root ")
            expression = expression.replace("sine", "sin")
            expression = expression.replace("cosine", "cos")
            expression = expression.replace("tangent", "tan")

            replacements = {
    "plus": "+",
    "add": "+",

    "minus": "-",
    "subtract": "-",

    "times": "×",
    "multiply": "×",
    "multiplied by": "×",

    "divide": "÷",
    "divided by": "÷",
    "over": "÷",

    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
}
            

            for word, symbol in replacements.items():
                expression = expression.replace(word, symbol)
            
            # sin
            expression = re.sub(
                r'sin (\d+)',
                r'sin(\1)',
                expression
            )

            # cos
            expression = re.sub(
                r'cos (\d+)',
                r'cos(\1)',
                expression
            )

            # tan
            expression = re.sub(
                r'tan (\d+)',
                r'tan(\1)',
                expression
            )
            
            # square root
            expression = re.sub(
                r'square root of (\d+)',
                r'sqrt(\1)',
                expression
            )

            expression = re.sub(
                r'root (\d+)',
                r'sqrt(\1)',
                expression
            )

            # factorial
            expression = re.sub(
                r'factorial of (\d+)',
                r'\1 factorial',
                expression
            )
            
            expression = re.sub(
                r'(\d+) factorial',
                r'\1!',
                expression
            )


            # log
            expression = re.sub(
                r'log (\d+)',
                r'log(\1)',
                expression
            )

            # ln
            expression = re.sub(
                r'ln (\d+)',
                r'ln(\1)',
                expression
            )
            
            expression = expression.replace(" ", "")
            
            self.mic_button.setText("🎤")
            self.expression.setText(expression)
            
            self.mic_timer.stop()
            self.mic_button.setText("🎤")

            self.calculate()

        except Exception as e:
            self.mic_timer.stop()
            self.mic_button.setText("🎤")

            print(e)
            self.answer.setText("Could not understand")
                
    def use_history(self, item):
        entry = item.text()

        expr = entry.split("=")[0].strip()

        self.expression.setText(expr)
        
    def save_history(self, entry):
        with open("history.txt", "a") as file:
            file.write(entry + "\n")
    
    def load_history(self):
        try:
            with open("history.txt", "r") as file:
                for line in file:
                    self.history.addItem(line.strip())
        except FileNotFoundError:
            pass
        
    def clear_history(self):
        self.history.clear()
  
        with open("history.txt", "w") as file:
            pass
        
    def speak(self, text):
        threading.Thread(
            target=self._speak_thread,
            args=(text,),
            daemon=True
        ).start()
        
    def _speak_thread(self, text):
        
        try:
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            
        except Exception as e:
            print("Speech Error:", e)
        
    def speak_answer(self, result):

        try:
            value = round(float(result),4)

            if value<0:
                speech = "minus" + num2words(abs(value))

            else:
                speech = num2words(
                    value
                )

            self.speak(f"The answer is {speech}")

        except:
            self.speak(f"The answer is {result}")
            
    def animate_mic(self):

        self.mic_button.setText(
            self.mic_frames[self.mic_index]
        )

        self.mic_index = (
            self.mic_index + 1
        ) % len(self.mic_frames)
        
    def show_help(self):

        help_text = """
VOICECALC COMMANDS

Basic Math
-----------
5 plus 6
10 minus 3
7 times 8
20 divided by 4

Scientific
-----------
sin 30
cos 60
tan 45
log 100
ln 10
square root of 144
root 144
5 factorial

Memory Commands
---------------
answer plus 5
ans plus 5
previous answer plus 5
last answer plus 5

double the answer
half the answer
half of the answer
square the answer

Constants
---------
pi
e

Examples
--------
what is 25 plus 17
calculate sin 30
find square root of 144
double the answer

Keyboard
--------
Enter = Calculate
Backspace = Delete

Voice
-----
🎤 Start Listening
🔊 Toggle Voice Output
"""

        QMessageBox.information(
            self,
            "VoiceCalc Help",
            help_text
        )

app = QApplication(sys.argv)

window = Calculator()
window.show()

sys.exit(app.exec())
