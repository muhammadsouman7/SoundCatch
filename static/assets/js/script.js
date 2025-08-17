const landingCard = document.getElementById('landingCard');
const downloaderCard = document.getElementById('downloaderCard');
const useSoundCatchBtn = document.getElementById('useSoundCatchBtn');

// Handle "Use SoundCatch" button click
useSoundCatchBtn.addEventListener('click', () => {
    // Fade out landing card
    landingCard.classList.remove('fade-in-card');
    landingCard.classList.add('fade-out-card');

    // Wait for fade-out animation to finish
    setTimeout(() => {
        landingCard.classList.add('d-none'); // hide landing card
        downloaderCard.classList.remove('d-none'); // show downloader card
        downloaderCard.classList.add('fade-in-card'); // fade in downloader card
    }, 700); // must match CSS animation duration
});

document.addEventListener('DOMContentLoaded', () => {
    const songInput = document.getElementById('songInput');
    const downloadBtn = document.getElementById('downloadBtn');
    const downloadForm = document.getElementById('downloadForm');
    const btnText = document.getElementById('btnText');
    const btnSpinner = document.getElementById('btnSpinner');
    const progressBarContainer = document.getElementById('progressBarContainer');
    const progressBar = document.getElementById('progressBar');

    let fIntervals;

    // Show button only when input has text
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

    // Handle form submission
    downloadForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const songName = songInput.value.trim();

        // Reset UI
        hideProgressBar();
        startFakeProgress(); // start fake progress bar
        downloadBtn.disabled = true;
        btnText.textContent = 'Downloading...';
        btnSpinner.classList.remove('d-none');

        const formData = new FormData(downloadForm);

        fetch(downloadForm.action, {
                method: 'POST',
                body: formData,
            })
            .then(response => {
                if (!response.ok) throw new Error('Network error');
                return response.blob();
            })
            .then(blob => {
                // Complete progress
                stopFakeProgress(true);

                // Safe filename from input
                const safeFilename = songName.replace(/[\\/*?:"<>|]/g, '');
                const filename = safeFilename ? `${safeFilename}.m4a` : 'song.m4a';

                // Trigger download
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            })
            .catch(error => {
                console.error('Download failed:', error);
                alert('Download failed. Please try again.');
                stopFakeProgress(false);
            })
            .finally(() => {
                downloadBtn.disabled = false;
                btnText.textContent = 'Download';
                btnSpinner.classList.add('d-none');
            });
    });

    // Hide progress bar
    function hideProgressBar() {
        clearInterval(fIntervals);
        progressBarContainer.classList.add('d-none');
        progressBar.style.width = '0%';
        progressBar.textContent = '';
        progressBar.classList.remove('bg-success');
    }

    // Fake progress bar
    function startFakeProgress() {
        let value = 0;
        progressBarContainer.classList.remove('d-none');
        fIntervals = setInterval(() => {
            if (value < 90) {
                value += Math.floor(Math.random() * 5) + 1;
                if (value > 90) value = 90;
                updateProgress(value);
            }
        }, 500);
    }

    // Stop progress bar
    function stopFakeProgress(success) {
        clearInterval(fIntervals);
        updateProgress(100);
        if (success) progressBar.classList.add('bg-success');
    }

    // Update progress bar
    function updateProgress(value) {
        progressBar.style.width = value + '%';
        progressBar.textContent = value + '%';
    }
});