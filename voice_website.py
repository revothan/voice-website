import os
import time
import webbrowser
import pyttsx3
from flask import Flask, send_from_directory, request
from dotenv import load_dotenv
import speech_recognition as sr
from openai import OpenAI
from colorama import Fore, Style, init
import shutil

# --------------------- Initialization ---------------------
init(autoreset=True)
load_dotenv()

API_KEY = os.getenv('OPENAI_API_KEY')
if not API_KEY:
    raise EnvironmentError("Error: OPENAI_API_KEY not found in environment variables.")
client = OpenAI(api_key=API_KEY)

engine = pyttsx3.init()

# --------------------- Utility Functions ---------------------
def type_effect(text, delay=0.05):
    """Simulate typing effect in the terminal."""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

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

# --------------------- Flask App Creation Function ---------------------
def create_flask_app(site_folder):
    """Create a new Flask app instance for each website."""
    app = Flask(__name__)
    
    @app.route('/')
    def serve_website():
        try:
            return send_from_directory(site_folder, "index.html")
        except FileNotFoundError:
            return "Website not generated yet. Please try generating one first."
        except Exception as e:
            return f"Error serving website: {str(e)}"
    
    return app

# --------------------- OpenAI Integration ---------------------
def generate_website(prompt):
    """Generate website code using OpenAI based on the given prompt."""
    type_effect(Fore.YELLOW + "Generating website code from OpenAI...")
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """You are an expert web developer creating modern, responsive websites. 
                Generate a complete, single HTML file that includes embedded CSS in the style tag and JavaScript in the script tag.
                Do not use markdown code blocks or language indicators.
                Do not include section markers or separators.
                Use Mockup Informations if needed such as business name, business product, the brand colors, etc.
                
                Requirements:
                - Include viewport meta tag for responsiveness
                - Use modern CSS features (flexbox/grid)
                - Ensure cross-browser compatibility
                - Include error handling in JavaScript
                - Add comments for clarity
                - Make the design mobile-responsive
                
                Format your response as a single complete HTML file with internal CSS and JS."""},
                {"role": "user", "content": f"Create a modern, responsive website with this description: {prompt}"}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        return {'html': response.choices[0].message.content}
    except Exception as e:
        type_effect(Fore.RED + f"Error generating website: {e}")
        return None

def parse_code_sections(code_text):
    """Extract HTML, CSS, and JS sections from the OpenAI response using improved parsing."""
    try:
        sections = {'html': '', 'css': '', 'js': ''}
        current_section = None
        
        lines = code_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            
            if '---HTML---' in line.upper():
                current_section = 'html'
                continue
            elif '---CSS---' in line.upper():
                current_section = 'css'
                continue
            elif '---JS---' in line.upper():
                current_section = 'js'
                continue
            elif '---END---' in line.upper():
                break
                
            if current_section and line:
                sections[current_section] += line + '\n'
        
        for key in sections:
            sections[key] = sections[key].strip()
            
        if not all(sections.values()):
            missing = [k for k, v in sections.items() if not v]
            raise ValueError(f"Missing or empty sections: {', '.join(missing)}")
            
        return sections
    except Exception as e:
        type_effect(Fore.RED + f"Error parsing code sections: {e}")
        return None

def save_website_files(code_sections, iteration):
    """Save the generated website files in a new folder for each iteration."""
    if not code_sections:
        return False, None

    try:
        site_folder = f"generated_site_{iteration}"
        
        if os.path.exists(site_folder):
            shutil.rmtree(site_folder)
        
        os.makedirs(site_folder)
        
        with open(f"{site_folder}/index.html", "w", encoding="utf-8") as f:
            f.write(code_sections['html'])
        return True, site_folder
    except Exception as e:
        type_effect(Fore.RED + f"Error saving files: {e}")
        return False, None

# --------------------- Main Program ---------------------
def main():
    """Main function with support for multiple website generations."""
    type_effect(Fore.CYAN + "Initializing Jarvis...")
    jarvis_speak("Hello, I am your virtual assistant. Ready for commands.")

    iteration = 1
    port_start = 5000

    while True:
        command = get_voice_command()
        if command:
            type_effect(Fore.CYAN + "Processing your command...")
            code_sections = generate_website(command)
            
            success, site_folder = save_website_files(code_sections, iteration)
            
            if success:
                port = port_start + iteration - 1
                url = f"http://127.0.0.1:{port}"
                type_effect(Fore.GREEN + f"Website {iteration} generated successfully. Launching preview at {url}...")
                
                app = create_flask_app(site_folder)
                webbrowser.open(url)
                
                try:
                    app.run(debug=False, port=port)
                except Exception as e:
                    type_effect(Fore.RED + f"Error running server: {e}")
                    continue

                jarvis_speak("Would you like to generate another website? Say yes or no.")
                type_effect(Fore.YELLOW + "Would you like to generate another website? (Say 'yes' or 'no')")
                
                retry = get_voice_command()
                if retry and 'yes' in retry.lower():
                    iteration += 1
                    continue
                else:
                    jarvis_speak("Thank you for using the website generator. Goodbye!")
                    type_effect(Fore.GREEN + "Thank you for using the website generator. Goodbye!")
                    break
            else:
                type_effect(Fore.YELLOW + "Would you like to try again? (Say 'yes' or 'no')")
                retry = get_voice_command()
                if not retry or 'no' in retry.lower():
                    jarvis_speak("Thank you for using the website generator. Goodbye!")
                    type_effect(Fore.GREEN + "Thank you for using the website generator. Goodbye!")
                    break
        else:
            type_effect(Fore.YELLOW + "Would you like to try again? (Say 'yes' or 'no')")
            retry = get_voice_command()
            if not retry or 'no' in retry.lower():
                jarvis_speak("Thank you for using the website generator. Goodbye!")
                type_effect(Fore.GREEN + "Thank you for using the website generator. Goodbye!")
                break

if __name__ == '__main__':
    main()