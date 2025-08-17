from flask import Flask, render_template, request, send_file
import yt_dlp
from io import BytesIO
import os
import re

app = Flask(__name__)

def makeSafeFilename(name):
    """Remove invalid characters from the filename to keep it safe."""
    return re.sub(r'[\\/*?:"<>|]', "", name)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Get the song name from the form
        songName = request.form.get("song")
        safeName = makeSafeFilename(songName)

        # yt-dlp options to grab the best audio (preferably m4a)
        ydlOpts = {
            "format": "bestaudio[ext=m4a]/bestaudio",
            "outtmpl": "%(title)s.%(ext)s"
        }

        # Download audio from YouTube based on the search query
        with yt_dlp.YoutubeDL(ydlOpts) as ydl:
            info = ydl.extract_info(f"ytsearch:{songName} song", download=True)
            filePath = ydl.prepare_filename(info["entries"][0])

        # Read the downloaded audio file into memory
        buffer = BytesIO()
        with open(filePath, "rb") as f:
            buffer.write(f.read())
        buffer.seek(0)

        # Remove the temporary file from disk
        os.remove(filePath)

        # Send the file back to the user as a download
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{safeName}.m4a",  # use the user's search as filename
            mimetype="audio/m4a"
        )

    # Render the index page for GET requests
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
