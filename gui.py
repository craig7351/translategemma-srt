import sys
import os
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QFileDialog, QComboBox, 
                             QTextEdit, QProgressBar, QSpinBox, QGroupBox, QFormLayout)
from PyQt6.QtCore import QThread, pyqtSignal, Qt

# Import backend logic
# Ensure the current directory is in sys.path to find translate_srt
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from translate_srt import translate_srt, translate_plain_text
import translate_srt as ts_module # to access prompt variable if needed (optional)

class TranslationWorker(QThread):
    progress_total = pyqtSignal(int, int) # processed files, total files
    progress_current_file = pyqtSignal(int, int) # processed lines, total lines
    log_msg = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, directory, output_directory, source_lang, target_lang, model, instruction, batch_size, file_mode="srt"):
        super().__init__()
        self.directory = directory
        self.output_directory = output_directory
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.model = model
        self.instruction = instruction
        self.batch_size = batch_size
        self.file_mode = file_mode.lower() # 'srt' or 'txt'
        self._is_running = True

    def run(self):
        target_ext = ".srt" if self.file_mode == "srt" else ".txt"
        files_to_process = []
        for root, dirs, files in os.walk(self.directory):
            for file in files:
                # Modified logic: don't skip _zh files necessarily if they are in input dir and we want to re-translate?
                # But generally skipping already translated files is good.
                # However, now we are outputting to a new folder.
                # If we are in input folder, we process everything ending with extension that doesn't look like a temp file.
                if file.lower().endswith(target_ext) and "_zh" not in file.lower():
                    files_to_process.append(os.path.join(root, file))
        
        total_files = len(files_to_process)
        if total_files == 0:
            self.log_msg.emit(f"未找到合適的 {target_ext} 檔案。")
            self.finished.emit()
            return

        self.log_msg.emit(f"找到 {total_files} 個檔案。開始翻譯...")
        self.log_msg.emit(f"輸出目錄: {self.output_directory}")
        
        for idx, file_path in enumerate(files_to_process):
            if not self._is_running:
                break
                
            file_name = os.path.basename(file_path)
            # Output path: output_directory / filename (same name)
            output_path = os.path.join(self.output_directory, file_name)
            
            self.log_msg.emit(f"[{idx+1}/{total_files}] 正在翻譯: {file_name} -> {os.path.basename(output_path)}")
            self.progress_total.emit(idx, total_files)
            
            # Reset file progress
            self.progress_current_file.emit(0, 100)
            
            # Helper for file progress
            def file_progress_cb(current, total):
                self.progress_current_file.emit(current, total)
                
            def log_cb(msg):
                self.log_msg.emit(f"  -> {msg}")

            try:
                if self.file_mode == "srt":
                    translate_srt(
                        file_path, 
                        source_lang=self.source_lang, 
                        target_lang=self.target_lang, 
                        model=self.model,
                        progress_callback=file_progress_cb,
                        log_callback=log_cb,
                        batch_size=self.batch_size,
                        instruction=self.instruction,
                        output_path=output_path
                    )
                else:
                    translate_plain_text(
                        file_path, 
                        source_lang=self.source_lang, 
                        target_lang=self.target_lang, 
                        model=self.model,
                        progress_callback=file_progress_cb,
                        log_callback=log_cb,
                        batch_size=self.batch_size,
                        instruction=self.instruction,
                        output_path=output_path
                    )
            except Exception as e:
                self.log_msg.emit(f"處理時發生錯誤 {os.path.basename(file_path)}: {e}")
                
            self.progress_total.emit(idx+1, total_files)
            
        self.log_msg.emit("所有任務已完成。")
        self.finished.emit()

    def stop(self):
        self._is_running = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Google Open Translate 翻譯工具 (作者: Book-Ai)")
        self.resize(800, 600)
        
        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 1. Paths Selection (Input & Output)
        paths_layout = QHBoxLayout()
        
        # Left: Input Source
        src_group = QGroupBox("檔案來源 (Input Source)")
        src_layout = QVBoxLayout() # Changed to VBox for better labeling if needed, strictly HBox is fine too
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("選擇輸入資料夾...")
        self.path_input.textChanged.connect(self.on_input_path_changed) # Auto-update output
        
        self.browse_btn = QPushButton("瀏覽輸入")
        self.browse_btn.clicked.connect(self.browse_folder)
        
        src_inner = QHBoxLayout()
        src_inner.addWidget(self.path_input)
        src_inner.addWidget(self.browse_btn)
        src_layout.addLayout(src_inner)
        src_group.setLayout(src_layout)
        
        # Right: Output Directory
        out_group = QGroupBox("輸出目錄 (Output Directory)")
        out_layout = QVBoxLayout()
        self.output_path_input = QLineEdit()
        self.output_path_input.setPlaceholderText("選擇輸出資料夾 (預設為同層 output)...")
        
        self.browse_out_btn = QPushButton("瀏覽輸出")
        self.browse_out_btn.clicked.connect(self.browse_output_folder)
        
        out_inner = QHBoxLayout()
        out_inner.addWidget(self.output_path_input)
        out_inner.addWidget(self.browse_out_btn)
        out_layout.addLayout(out_inner)
        out_group.setLayout(out_layout)
        
        paths_layout.addWidget(src_group)
        paths_layout.addWidget(out_group)
        
        main_layout.addLayout(paths_layout)
        
        # 2. Settings
        settings_group = QGroupBox("翻譯設定 (Settings)")
        settings_layout = QFormLayout()
        
        # Mode Selection
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["SRT 字幕 (.srt)", "一般文件 (.txt)"])
        settings_layout.addRow("檔案類型 (File Type):", self.mode_combo)
        
        self.model_combo = QComboBox()
        # Default options based on official library
        self.model_combo.addItems(["translategemma:27b", "translategemma:12b", "translategemma:4b"])
        self.model_combo.setEditable(True) 
        
        # Language Selection
        self.src_lang_input = QComboBox()
        self.src_lang_input.addItems(["English", "Traditional Chinese", "Japanese", "Korean"])
        self.src_lang_input.setEditable(True)
        self.src_lang_input.setCurrentText("English")
        
        self.tgt_lang_input = QComboBox()
        self.tgt_lang_input.addItems(["Traditional Chinese", "English", "Japanese", "Korean"])
        self.tgt_lang_input.setEditable(True)
        self.tgt_lang_input.setCurrentText("Traditional Chinese")
        
        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(1, 100)
        self.batch_spin.setValue(20)
        
        # PROMPT PRESETS
        self.prompts = {
            "情色小說 (Erotica)": "You are a professional erotica novel translator. Translate with the appropriate tone and nuance, ensuring the context of the scene is conveyed accurately.",
            "通用翻譯 (General)": "You are a professional translator. Translate with accuracy and natural flow, ensuring the target text is easy to read and grammatically correct.",
            "文學小說 (Literature)": "You are a professional literature translator. Focus on preserving the author's style, emotional depth, and rhetorical elegance.",
            "科技文件 (Technial)": "You are a professional technical translator. Ensure terminology accuracy, clarity, and conciseness.",
            "電影字幕 (Subtitle)": "You are a professional subtitle translator. Keep translations concise, natural, and suitable for reading speed, using spoken language style."
        }
        
        self.prompt_combo = QComboBox()
        self.prompt_combo.addItems(list(self.prompts.keys()))
        self.prompt_combo.setCurrentText("電影字幕 (Subtitle)")
        self.prompt_combo.currentIndexChanged.connect(self.update_prompt_text)
        
        self.app_instruction = QTextEdit()
        self.app_instruction.setPlaceholderText("請輸入或選擇系統 Prompt 指令...")
        self.app_instruction.setMaximumHeight(80)
        
        # Set default
        self.update_prompt_text()
        
        settings_layout.addRow("Ollama 模型 (Model):", self.model_combo)
        settings_layout.addRow("來源語言 (Source):", self.src_lang_input)
        settings_layout.addRow("目標語言 (Target):", self.tgt_lang_input)
        settings_layout.addRow("批次大小 (Batch Size):", self.batch_spin)
        settings_layout.addRow("風格預設 (Preset):", self.prompt_combo)
        settings_layout.addRow("翻譯指令 (Instruction):", self.app_instruction)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # 3. Actions
        action_layout = QHBoxLayout()
        self.start_btn = QPushButton("開始批量翻譯")
        self.start_btn.clicked.connect(self.start_translation)
        self.start_btn.setFixedHeight(40)
        # Apply style to make it prominent
        self.start_btn.setStyleSheet("font-weight: bold; font-size: 14px; background-color: #4CAF50; color: white;")
        
        action_layout.addWidget(self.start_btn)
        main_layout.addLayout(action_layout)
        
        # 4. Progress & Logs
        progress_group = QGroupBox("進度 (Progress)")
        progress_layout = QVBoxLayout()
        
        progress_layout.addWidget(QLabel("當前檔案進度:"))
        self.file_progress = QProgressBar()
        progress_layout.addWidget(self.file_progress)
        
        progress_layout.addWidget(QLabel("總進度:"))
        self.total_progress = QProgressBar()
        progress_layout.addWidget(self.total_progress)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        progress_layout.addWidget(self.log_output)
        
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        self.worker = None

        # Initialize models and prompts after UI is ready
        self.fetch_ollama_models()
        self.update_prompt_text()
        
        # Initialize models after UI is ready
        self.fetch_ollama_models()

    def fetch_ollama_models(self):
        try:
            import subprocess
            # Run ollama list
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, encoding='utf-8')
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                # Skip header
                if len(lines) > 1:
                    models = []
                    for line in lines[1:]:
                        parts = line.split()
                        if parts:
                            models.append(parts[0])
                    if models:
                        self.model_combo.clear()
                        self.model_combo.addItems(models)
                        self.log("已從 Ollama 獲取模型列表。")
                        # Select translategemma if available
                        idx = self.model_combo.findText("translategemma:latest")
                        if idx >= 0:
                            self.model_combo.setCurrentIndex(idx)
                        else:
                            # Try partial match
                            for i in range(self.model_combo.count()):
                                if "translategemma" in self.model_combo.itemText(i):
                                    self.model_combo.setCurrentIndex(i)
                                    break
        except Exception as e:
            self.log(f"無法獲取模型列表: {e}")

    def update_prompt_text(self):
        key = self.prompt_combo.currentText()
        if key in self.prompts:
            self.app_instruction.setPlainText(self.prompts[key])

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "選擇資料夾")
        if folder:
            # Normalize path separators to /
            folder = folder.replace(os.path.sep, "/")
            self.path_input.setText(folder)

    def browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "選擇輸出資料夾")
        if folder:
            # Normalize path separators to /
            folder = folder.replace(os.path.sep, "/")
            self.output_path_input.setText(folder)
            
    def on_input_path_changed(self, text):
        # Automatically suggest output folder if output is empty or looks like a default
        if text and os.path.isdir(text):
            # Default: sibling 'output' folder
            # If input is .../project/input, output -> .../project/output
            # If input is .../project, output -> .../project/output (subfolder? user said "same level output", usually implies sibling if input is a specific folder, or subfolder if input is root.
            # User said: "改左邊選來源 右邊選output目錄, 預設會是跟input同一層的目錄名output" -> Same level as input directory.
            # E.g. Input: F:/.../input -> Output: F:/.../output
            
            # Correct Logic:
            # If Input is "F:/0_CODE/google-open-translate/input" (a folder named 'input')
            # We want Output to be "F:/0_CODE/google-open-translate/output" (a sibling folder named 'output')
            
            # If Input is "F:/0_CODE/google-open-translate/my_project"
            # We want Output to be "F:/0_CODE/google-open-translate/my_project_output" OR "F:/0_CODE/google-open-translate/output" ?
            # User requirement: "預設會是跟input同一層的目錄名output" (Default should be a directory named "output" at the same level as "input")
            
            abs_input = os.path.abspath(text)
            parent_dir = os.path.dirname(abs_input)
            
            # So if input is .../A/B, output is .../A/output
            suggested_output = os.path.join(parent_dir, "output")
            # Normalize to /
            suggested_output = suggested_output.replace("\\", "/")
            self.output_path_input.setText(suggested_output)

    def log(self, message):
        self.log_output.append(message)
        # Scroll to bottom
        sb = self.log_output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def start_translation(self):
        directory = self.path_input.text().strip()
        output_directory = self.output_path_input.text().strip()
        
        if not directory or not os.path.isdir(directory):
            self.log("錯誤: 請選擇有效的輸入資料夾。")
            return
            
        if not output_directory:
             # Fallback or strict? Let's just create it if empty based on logic or ask user?
             # But on_input_path_changed should have populated it.
             self.log("錯誤: 請選擇有效的輸出資料夾。")
             return

        # Disable button
        self.start_btn.setEnabled(False)
        self.start_btn.setText("翻譯進行中...")
        
        # Init worker
        mode = "srt" if self.mode_combo.currentIndex() == 0 else "txt"
        
        self.worker = TranslationWorker(
            directory=directory,
            output_directory=output_directory,
            source_lang=self.src_lang_input.currentText(),
            target_lang=self.tgt_lang_input.currentText(),
            model=self.model_combo.currentText(),
            instruction=self.app_instruction.toPlainText(),
            batch_size=self.batch_spin.value(),
            file_mode=mode
        )
        
        self.worker.log_msg.connect(self.log)
        self.worker.progress_current_file.connect(self.file_progress.setValue)
        self.worker.progress_current_file.connect(lambda v, m: self.file_progress.setMaximum(m))
        self.worker.progress_total.connect(self.total_progress.setValue)
        self.worker.progress_total.connect(lambda v, m: self.total_progress.setMaximum(m))
        self.worker.finished.connect(self.on_finished)
        
        self.worker.start()

    def on_finished(self):
        self.start_btn.setEnabled(True)
        self.start_btn.setText("開始批量翻譯")
        self.log("作業完成。")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
