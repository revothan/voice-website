import os
import re
import webbrowser
import time
import pyttsx3
from flask import Flask, send_from_directory
import speech_recognition as sr
from dotenv import load_dotenv
from openai import OpenAI
from colorama import Fore, Back, Style, init

# Initialize Colorama
init(autoreset=True)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize pyttsx3 for text-to-speech
engine = pyttsx3.init()

def type_effect(text, delay=0.05):
    """Simulate typing effect in the terminal."""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()  # New line after the text

def jarvis_speak(text):
    """Simulate Jarvis speaking with pyttsx3."""
    engine.say(text)
    engine.runAndWait()

def get_voice_command():
    """Capture and return the user's voice command as text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        type_effect(Fore.CYAN + "Listening for your command...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
            command = recognizer.recognize_google(audio, language="id-ID")
            type_effect(Fore.GREEN + f"You said: {command}")
            return command
        except sr.UnknownValueError:
            type_effect(Fore.RED + "Sorry, I could not understand the audio.")
        except sr.RequestError as e:
            type_effect(Fore.RED + f"Could not process the request; {e}")
        except Exception as e:
            type_effect(Fore.RED + f"Error: {e}")
    return None

def generate_website(prompt):
    """Generate website code using OpenAI based on the given prompt."""
    type_effect(Fore.YELLOW + "Generating website code from OpenAI...")
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """You are an expert web developer creating modern, responsive websites. DO NOT use any markdown code blocks (```). Provide clean code without formatting markers. Follow these requirements strictly:
                1. Use modern CSS (Flexbox/Grid) for layouts
                2. Ensure mobile responsiveness
                3. Include hover states and smooth transitions
                4. Use semantic HTML5 elements
                5. Write clean, well-structured JavaScript
                6. Include proper error handling
                7. Add user feedback and status messages
                8. Use a professional color scheme."""},
                {"role": "user", "content": f"Create a modern, responsive website with this description: {prompt}. Provide clean code without any markdown formatting or code blocks."}
            ],
            temperature=0.2
        )
        return parse_code_sections(response.choices[0].message.content)
    except Exception as e:
        type_effect(Fore.RED + f"Error generating website: {e}")
    return None

def parse_code_sections(code_text):
    """Extract HTML, CSS, and JS sections from the OpenAI response."""
    try:
        html = re.search(r'\[HTML_START\](.*?)\[HTML_END\]', code_text, re.DOTALL)
        css = re.search(r'\[CSS_START\](.*?)\[CSS_END\]', code_text, re.DOTALL)
        js = re.search(r'\[JS_START\](.*?)\[JS_END\]', code_text, re.DOTALL)

        if not all([html, css, js]):
            raise ValueError("Could not parse all sections of the code")

        return {
            'html': html.group(1).strip(),
            'css': css.group(1).strip(),
            'js': js.group(1).strip()
        }
    except Exception as e:
        type_effect(Fore.RED + f"Error parsing code sections: {e}")
    return None

def save_website_files(code_sections):
    """Save the generated website files to the local directory."""
    if not code_sections:
        return False

    try:
        os.makedirs("generated_site", exist_ok=True)
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Website</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial, sans-serif; color: #333; line-height: 1.6; }}
        {code_sections['css']}
    </style>
</head>
<body>
    {code_sections['html']}
    <script>
        (function() {{ 'use strict'; {code_sections['js']} }})();
    </script>
</body>
</html>"""

        with open("generated_site/index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        return True
    except Exception as e:
        type_effect(Fore.RED + f"Error saving files: {e}")
    return False

@app.route('/')
def serve_website():
    """Serve the generated website on the root route."""
    try:
        return send_from_directory("generated_site", "index.html")
    except FileNotFoundError:
        return "Website not generated yet."

def main():
    """Main function to orchestrate the voice command to website generation."""
    if not os.getenv('OPENAI_API_KEY'):
        type_effect(Fore.RED + "Error: OPENAI_API_KEY not found in environment variables.")
        return

    type_effect(Fore.CYAN + "Initializing Jarvis...")

    # Simulate Jarvis "speaking"
    jarvis_speak("Hello, I am your virtual assistant. Ready for commands.")

    command = get_voice_command()
    if command:
        type_effect(Fore.CYAN + "Processing your command...")
        code_sections = generate_website(command)
        if code_sections and save_website_files(code_sections):
            url = "http://127.0.0.1:5000"
            type_effect(Fore.GREEN + f"Website generated successfully. Launching preview at {url}...")
            webbrowser.open(url)
            app.run(debug=False)
        else:
            type_effect(Fore.RED + "Failed to generate or save website code.")
    else:
        type_effect(Fore.RED + "No valid voice command provided.")

if __name__ == '__main__':
    main()
