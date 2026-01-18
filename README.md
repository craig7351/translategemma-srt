# Google Open Translate 翻譯工具 (作者: Book-Ai)

這是一個基於 Google **TranslateGemma** 模型 (透過 Ollama 運行) 的本地端自動翻譯工具。
專為處理 **SRT 字幕** 與 **純文字檔 (TXT)** 設計，結合了 LLM 的上下文理解能力與傳統演算法的精確性，提供流暢且高品質的翻譯體驗。

## ✨ 主要特色 (Features)

### 1. 🚀 本地端運行 (Local Privacy)
- 使用 `ollama` 運行 Google 開源的 `TranslateGemma` 模型。
- **無須聯網**，資料完全留在本地，適合處理機密或敏感內容。
- 無 API 使用費用。

### 2. 🧠 上下文感知批次翻譯 (Context-Aware)
- 支援 **Batch Processing**，將多行文本合併送入模型。
- 模型能理解對話的前後文關係，避免傳統逐行翻譯造成的語意斷裂 (Sentence Fragmentation)。

### 3. 🇹🇼 強制台灣正體中文 (OpenCC Integrated)
- 內建 **OpenCC (Open Chinese Convert)** 引擎。
- 當目標語言選擇「Traditional Chinese」時，系統會自動將翻譯結果進行 **強制繁簡轉換 (s2twp)**，確保輸出為純正的台灣正體中文，不會有簡體字混入。

### 4. 📂 智慧檔案管理 (Input/Output Separation)
- **來源與輸出分離**：支援設定不同的輸入與輸出資料夾，保持檔案整潔。
- **智慧預設**：選擇輸入資料夾後，自動建議同層級的 `output` 資料夾。
- **原檔名輸出**：翻譯後的檔案直接存入輸出目錄，維持原始檔名，方便後製作業。

### 5. 🎭 多語言與風格預設 (Presets & Multi-lang)
- **多語言支援**：介面內建 English, Traditional Chinese, Japanese, Korean 下拉選單 (亦可手動輸入其他語言)。
- **風格預設 (Presets)**：內建 5 種常用翻譯風格 Prompt：
    - 🔞 情色小說 (Erotica)
    - 🌏 通用翻譯 (General)
    - 📖 文學小說 (Literature)
    - 💻 科技文件 (Technical)
    - 🎬 電影字幕 (Subtitle)

## 🛠️ 安裝與設置 (Installation)

### 1. 安裝 Ollama
請至 [Ollama 官方網站](https://ollama.com/download) 下載並安裝 Ollama。
安裝後，請在終端機執行以下指令下載翻譯模型 (推薦 4B 或 12B)：

```bash
# 推薦 (速度與品質平衡)
ollama pull translategemma:12b
ollama pull translategemma:4b
```

### 2. 專案環境設置
本專案使用 Python 開發，建議使用虛擬環境：

```bash
# 1. 建立虛擬環境
python -m venv venv

# 2. 啟動虛擬環境 (Windows)
.\venv\Scripts\activate

# 3. 安裝依賴套件 (含 PyQt6, OpenCC, SRT 等)
pip install -r requirements.txt
```

## 💻 使用方法 (Usage)

### 啟動圖形介面 (GUI)

- **Windows**:
  雙擊目錄下的 `start.bat` 即可啟動程式。

- **macOS / Linux**:
  請打開終端機，執行以下指令：
  ```bash
  source venv/bin/activate
  python gui.py
  ```
1.  **Input Source**: 點擊「瀏覽輸入」選擇包含 SRT 或 TXT 檔案的資料夾。
2.  **Output Directory**: 程式會自動建議輸出路徑 (通常是同層的 `output` 資料夾)，您也可以點擊「瀏覽輸出」手動更改。
3.  **Translation Settings**:
    - **Ollama 模型**: 選擇已安裝的模型 (如 `translategemma:27b`)。
    - **來源/目標語言**: 使用下拉選單選擇 (支援 En/Zh-TW/Ja/Ko)。
    - **檔案類型**: 選擇 `.srt` (字幕) 或 `.txt` (純文字)。
    - **風格預設**: 依照內容類型選擇合適的 Prompt (例如翻譯小說可選 "Literature")。
4.  **Start**: 點擊「開始批量翻譯」，進度條會顯示當前檔案與總進度。

## 📋 專案結構
- `gui.py`: PyQt6 圖形介面主程式。
- `translate_srt.py`: 核心翻譯邏輯 (SRT/TXT 處理、Batch 分割)。
- `main.py`: Ollama API 串接與 OpenCC 後處理模組。
- `requirements.txt`: 專案依賴列表。

## ⚠️ 常見問題
- **翻譯出來有簡體字？**
    請檢查目標語言是否包含 "Traditional Chinese" 字樣。只有在目標語言為繁體中文時，OpenCC 強制轉換才會啟動。
- **速度太慢？**
    請嘗試將 Batch Size 調小 (例如 10)，或是改用參數較小的模型 (4b)。
