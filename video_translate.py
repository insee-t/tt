import argparse
import os
import subprocess
import tempfile
import re
import requests
import time
from funasr import AutoModel
from gtts import gTTS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def count_chinese_words(text):
    """Count Chinese characters (each character is considered a word)"""
    # Remove spaces, punctuation, and non-Chinese characters
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    return len(chinese_chars)

def count_thai_words(text):
    """Count Thai words (split by spaces and Thai word boundaries)"""
    # Remove punctuation and split by spaces
    words = re.findall(r'[\u0e00-\u0e7f]+', text)
    return len(words)

def count_english_words(text):
    """Count English words (split by whitespace)"""
    words = text.split()
    return len(words)

def extract_audio(video_path, audio_path):
    subprocess.run([
        'ffmpeg', '-y', '-i', video_path, '-vn', '-acodec', 'pcm_s16le', audio_path
    ], check=True)

def transcribe_audio(audio_path):
    """Transcribe audio using FunASR for better Chinese speech recognition"""
    try:
        # Initialize FunASR model with update check disabled
        model = AutoModel(model="paraformer-zh", disable_update=True)
        
        # Transcribe the audio
        result = model.generate(input=audio_path)
        
        # Extract the transcribed text
        if result and len(result) > 0:
            transcribed_text = result[0]['text']
            return transcribed_text
        else:
            print("Warning: No transcription result from FunASR")
            return ""
            
    except Exception as e:
        print(f"FunASR transcription error: {e}")
        return ""

def translate_text(text, target_lang="en"):
    """Translate text using Google Translate API to a specified language (default: English)"""
    try:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise Exception("GOOGLE_API_KEY not found in environment variables")
        url = "https://translation.googleapis.com/language/translate/v2"
        params = {
            'key': api_key,
            'q': text,
            'source': 'zh',
            'target': target_lang
        }
        response = requests.post(url, data=params)
        response.raise_for_status()
        result = response.json()
        translated_text = result['data']['translations'][0]['translatedText']
        return translated_text
    except Exception as e:
        print(f"Google Translate API error: {e}")
        return text

def text_to_speech(text, tts_path, speed_factor=1.0):
    """Convert text to speech"""
    try:
        # Use gTTS to generate speech
        tts = gTTS(text, lang='th', slow=False)
        tts.save(tts_path)
            
    except Exception as e:
        print(f"TTS error: {e}")
        # Fallback to normal TTS
        tts = gTTS(text, lang='th')
        tts.save(tts_path)

def get_video_duration(video_path):
    """Get video duration in seconds"""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', 
            '-of', 'csv=p=0', video_path
        ], capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except:
        return None

def get_audio_duration(audio_path):
    """Get audio duration in seconds"""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', 
            '-of', 'csv=p=0', audio_path
        ], capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except:
        return None

def calculate_optimal_speed(video_duration, audio_duration):
    """Calculate optimal speed factor to match video duration"""
    if video_duration and audio_duration and audio_duration > 0:
        # To make audio shorter, we need to speed it up
        # Speed factor = audio_duration / video_duration
        # If audio is longer than video, speed_factor > 1 (speed up)
        # If audio is shorter than video, speed_factor < 1 (slow down)
        return audio_duration / video_duration
    return 1.5  # Default speed factor (no change)

def replace_audio(video_path, audio_path, output_path):
    subprocess.run([
        'ffmpeg', '-y', '-i', video_path, '-i', audio_path, '-c:v', 'copy', '-map', '0:v:0', '-map', '1:a:0', '-shortest', output_path
    ], check=True)

def translate_english_to_thai_google(english_text):
    """Translate English to Thai using Google Translate API"""
    try:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise Exception("GOOGLE_API_KEY not found in environment variables")
        url = "https://translation.googleapis.com/language/translate/v2"
        params = {
            'key': api_key,
            'q': english_text,
            'source': 'en',
            'target': 'th'
        }
        response = requests.post(url, data=params)
        response.raise_for_status()
        result = response.json()
        translated_text = result['data']['translations'][0]['translatedText']
        return translated_text
    except Exception as e:
        print(f"Google Translate API error: {e}")
        print("Falling back to English text...")
        return english_text  # Return original text if translation fails

def main():
    # Start overall timer
    overall_start_time = time.time()
    
    parser = argparse.ArgumentParser(description='Translate Chinese video to Thai audio.')
    parser.add_argument('input_video', help='Path to input video file')
    parser.add_argument('output_video', help='Path to output video file')
    parser.add_argument('--thai_file', help='Path to Thai translation text file (optional, for manual translation)')
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_wav = os.path.join(tmpdir, 'audio.wav')
        thai_mp3 = os.path.join(tmpdir, 'thai.mp3')

        # Step 1: Extract audio
        step_start = time.time()
        print('Extracting audio...')
        extract_audio(args.input_video, audio_wav)
        step_time = time.time() - step_start
        print(f'✅ Audio extraction completed in {step_time:.1f} seconds')

        # Step 2: Transcribe Chinese speech
        step_start = time.time()
        print('Transcribing Chinese speech...')
        chinese_text = transcribe_audio(audio_wav)
        chinese_word_count = count_chinese_words(chinese_text)
        step_time = time.time() - step_start
        print(f'✅ Transcription completed in {step_time:.1f} seconds')
        print(f'Chinese text ({chinese_word_count} words): {chinese_text}')

        # Step 3: Translate to English
        step_start = time.time()
        print('Translating to English...')
        english_text = translate_text(chinese_text, target_lang="en")
        english_word_count = count_english_words(english_text)
        step_time = time.time() - step_start
        print(f'✅ English translation completed in {step_time:.1f} seconds')
        print(f'English text ({english_word_count} words): {english_text}')

        # Step 4: Handle Thai translation
        step_start = time.time()
        if args.thai_file and os.path.exists(args.thai_file):
            print(f'Using manual Thai translation from: {args.thai_file}')
            with open(args.thai_file, 'r', encoding='utf-8') as f:
                thai_text = f.read().strip()
        else:
            print('Translating English to Thai using Google Translate API...')
            thai_text = translate_english_to_thai_google(english_text)
            
            # If Google Translate failed and no manual file provided, save English text for manual translation
            if not re.search(r'[\u0e00-\u0e7f]', thai_text):
                print('\n⚠️  Google Translate API failed. English text saved for manual translation.')
                manual_file = 'english_for_translation.txt'
                with open(manual_file, 'w', encoding='utf-8') as f:
                    f.write(english_text)
                print(f'📝 English text saved to: {manual_file}')
                print('💡 Please translate this to Thai and save as "thai_translation.txt", then run:')
                print(f'   python video_translate.py {args.input_video} {args.output_video} --thai_file thai_translation.txt')
                return
        
        thai_word_count = count_thai_words(thai_text)
        step_time = time.time() - step_start
        print(f'✅ Thai translation completed in {step_time:.1f} seconds')
        print(f'Thai text ({thai_word_count} words): {thai_text}')

        # Step 5: Convert to speech and adjust speed
        step_start = time.time()
        print('Converting Thai text to speech...')
        video_duration = get_video_duration(args.input_video)
        print(f'Video duration: {video_duration:.1f} seconds')
        
        # Generate initial TTS
        text_to_speech(thai_text, thai_mp3)
        audio_duration = get_audio_duration(thai_mp3)
        print(f'Initial TTS duration: {audio_duration:.1f} seconds')
        
        # Calculate and apply speed adjustment if needed
        speed_factor = calculate_optimal_speed(video_duration, audio_duration)
        print(f'Calculated speed factor: {speed_factor:.2f}x')
        
        if speed_factor != 1.0:
            print(f'Adjusting audio speed to match video duration...')
            # Apply speed adjustment to existing audio file
            temp_mp3 = thai_mp3 + '.temp'
            os.rename(thai_mp3, temp_mp3)
            
            # Use ffmpeg to change speed without affecting pitch
            # atempo filter has limits (0.5x to 2.0x), so we need to chain multiple filters
            if speed_factor > 2.0:
                # For high speed factors, chain multiple atempo filters
                # Calculate how many 2.0x filters we need
                remaining_factor = speed_factor
                filter_chain = []
                while remaining_factor > 2.0:
                    filter_chain.append("atempo=2.0")
                    remaining_factor /= 2.0
                if remaining_factor > 1.0:
                    filter_chain.append(f"atempo={remaining_factor}")
                filter_str = ",".join(filter_chain)
                print(f'Using chained atempo filters: {filter_str}')
            elif speed_factor < 0.5:
                # For low speed factors, chain multiple atempo filters
                # Calculate how many 0.5x filters we need
                remaining_factor = speed_factor
                filter_chain = []
                while remaining_factor < 0.5:
                    filter_chain.append("atempo=0.5")
                    remaining_factor /= 0.5
                if remaining_factor < 1.0:
                    filter_chain.append(f"atempo={remaining_factor}")
                filter_str = ",".join(filter_chain)
                print(f'Using chained atempo filters: {filter_str}')
            else:
                filter_str = f'atempo={speed_factor}'
                print(f'Using single atempo filter: {filter_str}')
            
            try:
                subprocess.run([
                    'ffmpeg', '-y', '-i', temp_mp3, 
                    '-filter:a', filter_str, 
                    thai_mp3
                ], check=True, capture_output=True, text=True)
                
                # Clean up temp file
                os.remove(temp_mp3)
                
                # Verify final duration
                final_audio_duration = get_audio_duration(thai_mp3)
                print(f'Final TTS duration: {final_audio_duration:.1f} seconds')
                
                # Check if adjustment was successful
                if final_audio_duration and video_duration and abs(final_audio_duration - video_duration) > 1.0:
                    print(f'⚠️  Warning: Audio duration ({final_audio_duration:.1f}s) still differs significantly from video duration ({video_duration:.1f}s)')
                    print(f'   Speed factor applied: {speed_factor:.2f}x')
                    print(f'   Difference: {abs(final_audio_duration - video_duration):.1f} seconds')
                    
                    # If audio is still longer than video, try to truncate it
                    if final_audio_duration > video_duration + 1.0:
                        print(f'   Audio is still too long. Truncating to match video duration...')
                        try:
                            # Create a temporary file for truncation
                            temp_truncate = thai_mp3 + '.truncate'
                            os.rename(thai_mp3, temp_truncate)
                            
                            # Truncate audio to video duration
                            subprocess.run([
                                'ffmpeg', '-y', '-i', temp_truncate, 
                                '-t', str(video_duration), 
                                thai_mp3
                            ], check=True, capture_output=True, text=True)
                            
                            # Clean up temp file
                            os.remove(temp_truncate)
                            
                            # Verify final duration
                            final_audio_duration = get_audio_duration(thai_mp3)
                            print(f'   Final TTS duration after truncation: {final_audio_duration:.1f} seconds')
                            
                        except subprocess.CalledProcessError as e:
                            print(f'   ❌ Truncation failed: {e}')
                            print(f'   Using speed-adjusted audio as is')
                            # Restore the speed-adjusted file
                            os.rename(temp_truncate, thai_mp3)
            except subprocess.CalledProcessError as e:
                print(f'❌ Speed adjustment failed: {e}')
                print(f'   Trying alternative approach with rubberband filter...')
                
                # Fallback to rubberband filter if atempo fails
                try:
                    subprocess.run([
                        'ffmpeg', '-y', '-i', temp_mp3, 
                        '-filter:a', f'rubberband=tempo={speed_factor}', 
                        thai_mp3
                    ], check=True, capture_output=True, text=True)
                    
                    # Clean up temp file
                    os.remove(temp_mp3)
                    
                    # Verify final duration
                    final_audio_duration = get_audio_duration(thai_mp3)
                    print(f'Final TTS duration (rubberband): {final_audio_duration:.1f} seconds')
                    
                except subprocess.CalledProcessError as e2:
                    print(f'❌ Rubberband filter also failed: {e2}')
                    print(f'   Using original audio without speed adjustment')
                    # Restore original file
                    os.rename(temp_mp3, thai_mp3)
        else:
            print('No speed adjustment needed')
        
        step_time = time.time() - step_start
        print(f'✅ TTS generation completed in {step_time:.1f} seconds')

        # Step 6: Replace audio in video
        step_start = time.time()
        print('Replacing audio in video...')
        replace_audio(args.input_video, thai_mp3, args.output_video)
        step_time = time.time() - step_start
        print(f'✅ Video processing completed in {step_time:.1f} seconds')

        # Calculate total time
        total_time = time.time() - overall_start_time
        
        print('🎉 Done! Output saved to', args.output_video)
        print(f'\n📊 Summary:')
        print(f'Chinese words: {chinese_word_count}')
        print(f'English words: {english_word_count}')
        print(f'Thai words: {thai_word_count}')
        print(f'⏱️  Total execution time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)')

if __name__ == '__main__':
    main() 