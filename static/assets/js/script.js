// Grab references to the main cards and the button
const landingCard = document.getElementById('landingCard');
const downloaderCard = document.getElementById('downloaderCard');
const useSoundCatchBtn = document.getElementById('useSoundCatchBtn');

// When the "Use SoundCatch" button is clicked
useSoundCatchBtn.addEventListener('click', () => {
    // Start by fading out the landing card
    landingCard.classList.remove('fade-in-card');
    landingCard.classList.add('fade-out-card');

    // Give the fade-out animation time to finish before switching views (700ms)
    setTimeout(() => {
        // Completely hide the landing card
        landingCard.classList.add('d-none');
        // Make the downloader card visible
        downloaderCard.classList.remove('d-none');
        // Animate the downloader card so it fades in smoothly
        downloaderCard.classList.add('fade-in-card');
    }, 700); // This number should always match the CSS animation duration
});

// Run after the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // Grab references to form elements and UI pieces
    const songInput = document.getElementById('songInput');
    const downloadBtn = document.getElementById('downloadBtn');
    const downloadForm = document.getElementById('downloadForm');
    const btnText = document.getElementById('btnText');
    const btnSpinner = document.getElementById('btnSpinner');
    const progressBarContainer = document.getElementById('progressBarContainer');
    const progressBar = document.getElementById('progressBar');

    let fIntervals; // Will hold the fake progress interval

    // Only show the "Download" button if the user has typed something
    songInput.addEventListener('input', () => {
        if (songInput.value.trim().length > 0) {
            downloadBtn.classList.remove('d-none');
            downloadBtn.classList.add('fade-in');
        } else {
            downloadBtn.classList.add('d-none');
            downloadBtn.classList.remove('fade-in');
            hideProgressBar();
        }
    });

    // Handle the form submission (downloading process)
    downloadForm.addEventListener('submit', (e) => {
        e.preventDefault(); // Don’t reload the page

        // Reset the UI before starting a new download
        hideProgressBar();
        startFakeProgress(); // Begin fake progress animation
        downloadBtn.disabled = true;
        btnText.textContent = 'Fetching the song...';
        btnSpinner.classList.remove('d-none');

        const formData = new FormData(downloadForm);

        // Step 1: Ask the backend for the actual audio URL and filename
        fetch(downloadForm.action, {
                method: 'POST',
                body: formData,
            })
            .then(response => {
                if (!response.ok) {
                    // If backend sends an error, read it and throw so it goes to catch()
                    return response.json().then(err => { throw new Error(err.error) });
                }
                return response.json();
            })
            .then(data => {
                // Make sure backend gave us both audio_url and filename
                if (!data.audio_url || !data.filename) {
                    throw new Error("Invalid response from server.");
                }

                // Step 2: Create a new URL to trigger the actual download
                const downloadUrl = `/download_audio?url=${encodeURIComponent(data.audio_url)}&filename=${encodeURIComponent(data.filename)}`;

                // Navigating to this URL will start the download automatically
                window.location.href = downloadUrl;

                // Since we’ve triggered the download, we assume success
                stopFakeProgress(true);
            })
            .catch((error) => {
                // If anything goes wrong, log it and let the user know
                console.error('Download failed:', error);
                alert(`Download failed: ${error.message}. Please try again.`);
                stopFakeProgress(false);
            });
    });

    // Hide and reset the progress bar
    function hideProgressBar() {
        clearInterval(fIntervals);
        progressBarContainer.classList.add('d-none');
        progressBar.style.width = '0%';
        progressBar.textContent = '';
    }

    // Start showing a "fake" progress bar to make the UI feel responsive
    function startFakeProgress() {
        let value = 0;
        progressBarContainer.classList.remove('d-none');
        fIntervals = setInterval(() => {
            // Only increase progress until 90% so it feels like it’s "loading"
            if (value < 90) {
                value += Math.floor(Math.random() * 4) + 1;
                if (value > 90) value = 90;
                updateProgress(value);
            }
        }, 500); // Update every half a second
    }

    // Stop the fake progress and handle success/failure UI
    function stopFakeProgress(success) {
        clearInterval(fIntervals);
        updateProgress(100); // Fill the bar

        if (success) {
            progressBar.classList.add('bg-success');
            btnText.textContent = 'Download Started!';
            btnSpinner.classList.add('d-none');

            // After a few seconds, reset everything back
            setTimeout(() => {
                btnText.textContent = 'Download';
                downloadBtn.disabled = false;
                progressBar.classList.remove('bg-success');
            }, 3000);
        } else {
            // On failure, just reset button states
            btnText.textContent = 'Download';
            btnSpinner.classList.add('d-none');
            downloadBtn.disabled = false;
        }
    }

    // Update progress bar visually
    function updateProgress(value) {
        progressBar.style.width = value + '%';
        progressBar.textContent = value + '%';
    }
});
