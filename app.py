from flask import Flask, render_template, request, jsonify, Response
import yt_dlp
import re
from flask_cors import CORS
import requests
import io
import os
import tempfile

app = Flask(__name__)
# CORS is crucial for allowing the frontend to make requests
CORS(app)

def makeSafeFilename(name):
    """
    Removes invalid characters from a string to make it a safe filename.
    """
    return re.sub(r'[\\/*?:"<>|]', "", name)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        songName = request.form.get("song")
        if not songName:
            return jsonify({"error": "Song name not provided."}), 400

        try:
            # Check if cookies are available from Vercel's environment variables
            cookies = os.environ.get("groot")
            if not cookies:
                return jsonify({"error": "Cookies not found. Please add cookies to Vercel environment variables with the name 'groot'."}), 500

            # Use a temporary file to store cookies since the file system is read-only
            # We explicitly use /tmp which is writable on Vercel.
            with tempfile.NamedTemporaryFile(mode='w', delete=False, dir='/tmp') as temp_cookies_file:
                temp_cookies_file.write(cookies)
                cookies_path = temp_cookies_file.name

            # yt-dlp options to find the best audio format without downloading
            ydlOpts = {
                # Prioritize m4a, mp3, and then the best available audio format.
                "format": "bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best",
                "noplaylist": True,
                "quiet": True,
                "logger": None,
                "default_search": "ytsearch",
                "extract_flat": "in_playlist", # Speeds up searches
                "socket_timeout": 60, # Set a 60-second timeout for network requests
                "cookiefile": cookies_path, # Pass the path to the temporary cookie file
            }

            with yt_dlp.YoutubeDL(ydlOpts) as ydl:
                # Search for the video and get its info
                info = ydl.extract_info(f"{songName} song", download=False)

                if not info or "entries" not in info or not info["entries"]:
                    return jsonify({"error": "Could not find a video for that song."}), 404

                # Get the URL of the best audio stream
                best_audio_stream = ydl.extract_info(info["entries"][0]["url"], download=False, process=True)
                
                audio_url = None
                file_ext = 'mp3'
                
                # We'll rely on yt-dlp to give us the best audio format directly
                if 'url' in best_audio_stream and 'ext' in best_audio_stream:
                    audio_url = best_audio_stream['url']
                    file_ext = best_audio_stream['ext']
                
                if not audio_url:
                    return jsonify({"error": "No suitable audio stream found."}), 404

                # Get the title for the filename from user input (more relevant and cleaner)
                title_for_filename = request.form.get("song", "song")
                safeName = makeSafeFilename(title_for_filename)

                # Send the direct URL and filename back to the frontend
                return jsonify({
                    "audio_url": audio_url,
                    "filename": f"{safeName}.{file_ext}"
                }), 200

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500
        finally:
            if 'cookies_path' in locals() and os.path.exists(cookies_path):
                os.remove(cookies_path)

    return render_template("index.html")

# New route to handle the actual download
@app.route("/download_audio", methods=["GET"])
def download_audio():
    audio_url = request.args.get('url')
    filename = request.args.get('filename')

    if not audio_url or not filename:
        return "URL or filename not provided", 400

    try:
        # Stream the file from the external URL to the Flask app, allowing redirects
        # and setting a timeout to prevent an indefinite wait.
        response = requests.get(audio_url, stream=True, allow_redirects=True, timeout=60)
        response.raise_for_status() # Raise an exception for bad status codes

        # This part now streams the content directly to the client
        def generate_chunks():
            for chunk in response.iter_content(chunk_size=8192):
                yield chunk

        return Response(
            generate_chunks(),
            mimetype=response.headers['Content-Type'],
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        return "Failed to download the audio file.", 500

if __name__ == "__main__":
    app.run(debug=True)
