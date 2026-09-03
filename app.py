from flask import Flask, render_template, request, jsonify, send_file, after_this_request
from flask_cors import CORS
import yt_dlp
from moviepy import AudioFileClip  # Uses AudioFileClip for fast conversion
import os
import tempfile
import urllib.parse

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# 1. Search Route
@app.route("/search", methods=["POST"])
def search_video():
    query = request.form.get("audio", "").strip()
    if not query:
        return jsonify({"error": "Please enter a search query."}), 400

    try:
        if query.startswith(("http://", "https://", "www.")):
            search_target = query
        else:
            search_target = f"ytsearch1:{query}"

        ydl_opts = {
            'quiet': True,
            'extract_flat': 'in_playlist',
            'skip_download': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_target, download=False)
            
            if not info:
                return jsonify({"error": "No results found on YouTube."}), 404

            if 'entries' in info and info['entries']:
                valid_entries = [e for e in info['entries'] if e]
                if not valid_entries:
                    return jsonify({"error": "No results found on YouTube."}), 404
                first_result = valid_entries[0]
            else:
                first_result = info

            video_id = first_result.get('id')
            title = first_result.get('title', query)
            watch_url = first_result.get('webpage_url') or f"https://www.youtube.com/watch?v={video_id}"

            if not video_id:
                return jsonify({"error": "Could not parse video details."}), 500

            return jsonify({
                "video_id": video_id,
                "title": title,
                "watch_url": watch_url
            }), 200

    except Exception as e:
        return jsonify({"error": f"Search error: {str(e)}"}), 500

# 2. Process Download Route (Direct Best Audio / Flexible Video)
@app.route("/process_download", methods=["POST"])
def process_download():
    watch_url = request.form.get("watch_url")
    format_type = request.form.get("format_type", "audio")

    if not watch_url:
        return jsonify({"error": "Invalid video URL."}), 400

    try:
        temp_dir = tempfile.mkdtemp()
        output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')

        # Select formats flexibly without hardcoding single-stream MP4 requirements
        if format_type == "audio":
            selected_format = 'bestaudio/best'
        else:
            selected_format = 'bestvideo+bestaudio/best'

        ydl_opts = {
            'outtmpl': output_template,
            'format': selected_format,
            'quiet': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(watch_url, download=True)
            downloaded_file = ydl.prepare_filename(info)

        # If audio requested, convert downloaded audio stream (m4a/webm) directly to MP3
        if format_type == "audio":
            audio_path = os.path.splitext(downloaded_file)[0] + ".mp3"
            
            # Using AudioFileClip is lighter and faster than VideoFileClip
            clip = AudioFileClip(downloaded_file)
            clip.write_audiofile(audio_path, logger=None)
            clip.close()

            # Clean up the raw downloaded audio file
            if os.path.exists(downloaded_file) and downloaded_file != audio_path:
                os.remove(downloaded_file)

            final_file = audio_path
        else:
            final_file = downloaded_file

        return jsonify({
            "download_url": f"/get_file?path={urllib.parse.quote(final_file)}",
            "filename": os.path.basename(final_file)
        }), 200

    except Exception as e:
        return jsonify({"error": f"Processing error: {str(e)}"}), 500

@app.route("/get_file", methods=["GET"])
def get_file():
    file_path = urllib.parse.unquote(request.args.get("path", ""))
    
    if not file_path or not os.path.exists(file_path):
        return "File not found", 404

    @after_this_request
    def remove_file(response):
        try:
            os.remove(file_path)
            os.rmdir(os.path.dirname(file_path))
        except Exception:
            pass
        return response

    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)