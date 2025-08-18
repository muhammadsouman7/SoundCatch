from flask import Flask, render_template, request, jsonify, send_file, Response
import yt_dlp
import re
from flask_cors import CORS
import requests
import io

app = Flask(__name__)
# Enable CORS so the frontend can talk to this backend without being blocked
CORS(app)

def makeSafeFilename(name):
    """
    Clean up a string so it can safely be used as a filename.
    Removes characters that are invalid in filenames.
    """
    return re.sub(r'[\\/*?:"<>|]', "", name)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        songName = request.form.get("song")
        if not songName:
            return jsonify({"error": "Song name not provided."}), 400

        try:
            # yt-dlp configuration: only fetch metadata (no actual download)
            ydlOpts = {
                # Prefer m4a > mp3 > any best audio format
                "format": "bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best",
                "noplaylist": True,       # Don’t fetch entire playlists
                "quiet": True,            # Suppress console output
                "logger": None,
                "default_search": "ytsearch",   # Search on YouTube if only a query is given
                "extract_flat": "in_playlist",  # Faster searches, avoids deep playlist info
                "socket_timeout": 60            # Timeout for network requests
            }

            with yt_dlp.YoutubeDL(ydlOpts) as ydl:
                # Search YouTube for the given song
                info = ydl.extract_info(f"{songName} song", download=False)

                # If no video was found, return an error
                if not info or "entries" not in info or not info["entries"]:
                    return jsonify({"error": "Could not find a video for that song."}), 404

                # Grab the best audio stream from the first search result
                best_audio_stream = ydl.extract_info(info["entries"][0]["url"], download=False, process=True)
                
                audio_url = None
                file_ext = 'mp3'
                
                # yt-dlp usually provides the stream URL and file extension
                if 'url' in best_audio_stream and 'ext' in best_audio_stream:
                    audio_url = best_audio_stream['url']
                    file_ext = best_audio_stream['ext']
                
                if not audio_url:
                    return jsonify({"error": "No suitable audio stream found."}), 404

                # Use the user’s query as the filename (cleaned for safety)
                title_for_filename = request.form.get("song", "song")
                safeName = makeSafeFilename(title_for_filename)

                # Return the stream URL and safe filename to the frontend
                return jsonify({
                    "audio_url": audio_url,
                    "filename": f"{safeName}.{file_ext}"
                }), 200

        except Exception as e:
            # Catch any unexpected errors and return them
            print(f"An error occurred: {str(e)}")
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    # For GET requests, just render the main page
    return render_template("index.html")

# Route to actually download the audio file
@app.route("/download_audio", methods=["GET"])
def download_audio():
    audio_url = request.args.get('url')
    filename = request.args.get('filename')

    if not audio_url or not filename:
        return "URL or filename not provided", 400

    try:
        # Stream the file directly from the given URL
        response = requests.get(audio_url, stream=True, allow_redirects=True, timeout=60)
        response.raise_for_status()  # If the response is bad, raise an error

        # Yield the file in chunks instead of loading it all in memory
        def generate_chunks():
            for chunk in response.iter_content(chunk_size=8192):
                yield chunk

        # Send the file back to the browser with proper headers
        return Response(
            generate_chunks(),
            mimetype=response.headers['Content-Type'],
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except requests.exceptions.RequestException as e:
        # If something goes wrong while fetching the file
        print(f"Error downloading file: {e}")
        return "Failed to download the audio file.", 500

if __name__ == "__main__":
    app.run(debug=True)
