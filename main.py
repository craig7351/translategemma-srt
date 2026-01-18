import ollama
import sys
import opencc

def translate(text, source_lang, target_lang, source_code=None, target_code=None, model='translategemma', instruction=None):
    """
    Translates text using the TranslateGemma model via Ollama.
    
    Args:
        text (str or list): The text or list of texts to translate.
        source_lang (str): The source language name (e.g., 'English').
        target_lang (str): The target language name (e.g., 'Traditional Chinese').
        source_code (str, optional): The ISO code for source language (e.g., 'en'). Defaults to None.
        target_code (str, optional): The ISO code for target language (e.g., 'zh-TW'). Defaults to None.
        model (str): The Ollama model to use. Defaults to 'translategemma'.
        instruction (str, optional): Additional instruction/persona for the translator.
        
    Returns:
        str or list: The translated text(s).
    """
    
    # Simple mapping for common codes if not provided
    code_map = {
        'English': 'en',
        'Traditional Chinese': 'zh-Hant',
        'Simplified Chinese': 'zh-Hans',
        'Japanese': 'ja',
        'Korean': 'ko',
        'French': 'fr',
        'German': 'de',
        'Spanish': 'es'
    }
    
    if not source_code:
        source_code = code_map.get(source_lang, 'unknown')
    if not target_code:
        target_code = code_map.get(target_lang, 'unknown')

    # Determine if input is a batch
    is_batch = isinstance(text, list)
    
    # Prepare content for prompt
    if is_batch:
        content_to_translate = "\n".join(text)
        batch_instruction = "The following input contains multiple lines of text. Please translate each line efficiently and maintain the original line breaks in your output. Do not merge lines."
    else:
        content_to_translate = text
        batch_instruction = ""

    # Persona / Instruction setup
    base_persona = f"You are a professional {source_lang} ({source_code}) to {target_lang} ({target_code}) translator."
    if instruction:
        base_persona += f" {instruction}"
        
    system_prompt = f"""{base_persona} Your goal is to accurately convey the meaning and nuances of the original {source_lang} text while adhering to {target_lang} grammar, vocabulary, and cultural sensitivities. {batch_instruction} Produce only the {target_lang} translation, without any additional explanations or commentary. Please translate the following {source_lang} text into {target_lang}:\n\n{content_to_translate}"""

    try:
        response = ollama.chat(model=model, messages=[
            {
                'role': 'user',
                'content': system_prompt,
            },
        ])
        result = response['message']['content'].strip()
        
        if is_batch:
            # Split result back into list
            translated_lines = result.split('\n')
            # Handle potential mismatch in line counts (basic fallback)
            if len(translated_lines) != len(text):
                # If mismatch, we might need a fallback or just return as is (could likely return mismatched list)
                # For now, let's just strip empty lines which sometimes happen
                translated_lines = [line for line in translated_lines if line.strip()]
                # If still mismatched, we can't do much without complex alignment.
            
            # Post-process: Force Traditional Chinese if requested
            if "Traditional Chinese" in target_lang:
                converter = opencc.OpenCC('s2twp')
                translated_lines = [converter.convert(line) for line in translated_lines]

            return translated_lines
        else:
             # Post-process: Force Traditional Chinese if requested
            if "Traditional Chinese" in target_lang:
                converter = opencc.OpenCC('s2twp')
                result = converter.convert(result)
            return result

    except Exception as e:
        return f"Error during translation: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # CLI usage: python main.py "Text to translate" "Source Lang" "Target Lang" [Instruction]
        if len(sys.argv) >= 4:
            text_arg = sys.argv[1]
            src_arg = sys.argv[2]
            tgt_arg = sys.argv[3]
            instr_arg = sys.argv[4] if len(sys.argv) > 4 else None
            
            print(f"Translating '{text_arg}' from {src_arg} to {tgt_arg}...")
            if instr_arg:
                print(f"Instruction: {instr_arg}")
            print("-" * 30)
            print(translate(text_arg, src_arg, tgt_arg, instruction=instr_arg))
        else:
             print("Usage: python main.py \"Text\" \"Source Lang\" \"Target Lang\" [Instruction]")
    else:
        # Default test
        test_batch = ["Hello world.", "How are you today?", "This is a batch test."]
        src = "English"
        tgt = "Traditional Chinese"
        
        print(f"Running batch test: {test_batch}")
        print("-" * 30)
        result = translate(test_batch, src, tgt)
        for original, translated in zip(test_batch, result):
            print(f"{original} -> {translated}")
