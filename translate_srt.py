import srt
import sys
import os
from tqdm import tqdm
from main import translate

def translate_srt(file_path, source_lang="English", target_lang="Traditional Chinese", model="translategemma", progress_callback=None, log_callback=None, batch_size=20, instruction=None, output_path=None):
    """
    Reads an SRT file, translates its content, and saves it as a new file.
    Args:
        output_path (str, optional): Full path for the output file. If None, uses default suffix _zh.
    """
    
    # Configuration
    BATCH_SIZE = batch_size
    INSTRUCTION = instruction
    
    if not INSTRUCTION:
         INSTRUCTION = "You are a professional erotica novel translator. Translate with the appropriate tone and nuance, ensuring the context of the scene is conveyed accurately."

    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    log(f"Reading {file_path}...")
    try:
        # Detect encoding or just assume utf-8/utf-8-sig
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read() 
    except UnicodeDecodeError:
        try:
             with open(file_path, "r", encoding="utf-8-sig") as f:
                content = f.read()
        except:
            log(f"Error reading file {file_path}. Is it UTF-8?")
            return

    try:
        subs = list(srt.parse(content))
    except Exception as e:
        log(f"Error parsing SRT: {e}")
        return

    log(f"Translating {len(subs)} subtitles from {source_lang} to {target_lang}...")
    
    new_subs = []
    current_progress = 0
    
    # Determine if we should use tqdm (disable in GUI or if no console)
    use_tqdm = True
    if log_callback is not None:
        use_tqdm = False
    if sys.stderr is None:
        use_tqdm = False

    iterator = range(0, len(subs), BATCH_SIZE)
    if use_tqdm:
         iterator = tqdm(iterator, unit="batch")

    for i in iterator:
        batch = subs[i : i + BATCH_SIZE]
        
        # specific fix: skip completely empty subs to avoid misalignment (or handle carefully)
        texts_to_translate = [sub.content.strip() for sub in batch]
        
        # If all texts in batch are empty, just skip (optimization)
        if not any(texts_to_translate):
            new_subs.extend(batch)
            current_progress += len(batch)
            if progress_callback:
                progress_callback(current_progress, len(subs))
            continue
            
        # Perform batch translation
        translated_texts = translate(texts_to_translate, source_lang, target_lang, model=model, instruction=INSTRUCTION)
        
        # If result is a single string (error or single line),
        # If result is a single string (error or single line),
        if isinstance(translated_texts, str):
             # If error message
             if "Error" in translated_texts:
                 log(f"Batch error: {translated_texts}")
                 translated_texts = texts_to_translate # Fallback
             else:
                 translated_texts = [translated_texts]
        
        # Ensure length matches (sometimes LLM merges lines)
        while len(translated_texts) < len(batch):
            translated_texts.append("")
            
        for idx, sub in enumerate(batch):
            if idx < len(translated_texts):
                sub.content = translated_texts[idx]
            new_subs.append(sub)
                
        current_progress += len(batch)
        if progress_callback:
            progress_callback(current_progress, len(subs))

    # Generate output filename
    if output_path is None:
        base_name, ext = os.path.splitext(file_path)
        output_path = f"{base_name}_zh{ext}"
    
    # Ensure output directory exists if output_path is provided
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    log(f"Saving translated SRT to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(new_subs))

    log("Done!")

def translate_plain_text(file_path, source_lang="English", target_lang="Traditional Chinese", model="translategemma", progress_callback=None, log_callback=None, batch_size=20, instruction=None, output_path=None):
    """
    Reads a text file, translates its content, and saves it as a new file.
    Args:
         output_path (str, optional): Full path for the output file.
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)
            
    if not os.path.exists(file_path):
        log(f"Error: File not found: {file_path}")
        return

    log(f"Reading {file_path}...")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        log(f"Error reading file: {e}")
        return

    log(f"Translating {len(lines)} lines from {source_lang} to {target_lang}...")
    
    # Configuration
    BATCH_SIZE = batch_size
    INSTRUCTION = instruction
    if not INSTRUCTION:
         INSTRUCTION = "You are a professional translator."

    translated_lines_map = {} # index -> translated text
    
    # Identify non-empty lines to translate
    lines_to_process = []
    for idx, line in enumerate(lines):
        if line.strip():
            lines_to_process.append((idx, line.strip()))
            
    total_items = len(lines_to_process)
    current_progress = 0
    
    # Determine if we should use tqdm (disable in GUI or if no console)
    use_tqdm = True
    if log_callback is not None:
        use_tqdm = False
    if sys.stderr is None:
        use_tqdm = False

    iterator = range(0, total_items, BATCH_SIZE)
    if use_tqdm:
        iterator = tqdm(iterator, unit="batch")

    # Process in batches
    for i in iterator:
        batch_tuples = lines_to_process[i : i + BATCH_SIZE]
        batch_indices = [t[0] for t in batch_tuples]
        batch_texts = [t[1] for t in batch_tuples]
        
        # Translate
        translated_results = translate(batch_texts, source_lang, target_lang, model=model, instruction=INSTRUCTION)
        
        # Handle single result or error
        if isinstance(translated_results, str):
             if "Error" in translated_results:
                 log(f"Batch error: {translated_results}")
                 translated_results = batch_texts
             else:
                 translated_results = [translated_results]
        
        # Safety fill
        while len(translated_results) < len(batch_texts):
             translated_results.append("")
             
        # Map back
        for idx_in_batch, trans_text in enumerate(translated_results):
            if idx_in_batch < len(batch_indices):
                original_idx = batch_indices[idx_in_batch]
                translated_lines_map[original_idx] = trans_text
                
        current_progress += len(batch_tuples)
        if progress_callback:
            progress_callback(current_progress, total_items)

    # Reconstruct file
    output_lines = []
    for idx, line in enumerate(lines):
        if idx in translated_lines_map:
            output_lines.append(translated_lines_map[idx] + "\n")
        else:
            output_lines.append(line) # Keep original empty lines or whitespace

    # Generate output filename
    if output_path is None:
        base_name, ext = os.path.splitext(file_path)
        output_path = f"{base_name}_zh{ext}"

    # Ensure output directory exists if output_path is provided
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    log(f"Saving translated text to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(output_lines)

    log("Done!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python translate_srt.py <file_path> [source_lang] [target_lang]")
    else:
        file_path = sys.argv[1]
        source = sys.argv[2] if len(sys.argv) > 2 else "English"
        target = sys.argv[3] if len(sys.argv) > 3 else "Traditional Chinese"
        translate_srt(file_path, source, target)
