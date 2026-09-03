document.addEventListener('DOMContentLoaded', () => {
    // 1. Landing Page Card Transition Logic
    const landingCard = document.getElementById('landingCard');
    const downloaderCard = document.getElementById('downloaderCard');
    const useSoundCatchBtn = document.getElementById('useSoundCatchBtn');

    if (useSoundCatchBtn) {
        useSoundCatchBtn.addEventListener('click', () => {
            landingCard.classList.remove('fade-in-card');
            landingCard.classList.add('fade-out-card');

            setTimeout(() => {
                landingCard.classList.add('d-none');
                downloaderCard.classList.remove('d-none');
                downloaderCard.classList.add('fade-in-card');
            }, 700);
        });
    }

    // 2. Downloader Elements
    const audioInput = document.getElementById('audioInput');
    const searchBtn = document.getElementById('searchBtn');
    const downloadForm = document.getElementById('downloadForm');
    const videoContainer = document.getElementById('videoContainer');
    const youtubeEmbed = document.getElementById('youtubeEmbed');
    const downloadControls = document.getElementById('downloadControls');
    const downloadBtn = document.getElementById('downloadBtn');
    const btnText = document.getElementById('btnText');
    const btnSpinner = document.getElementById('btnSpinner');
    const progressBarContainer = document.getElementById('progressBarContainer');
    const progressBar = document.getElementById('progressBar');

    let currentWatchUrl = '';
    let fIntervals;

    // Phase 1: Search video and display embed
    searchBtn.addEventListener('click', () => {
        const query = audioInput.value.trim();
        if (!query) return;

        searchBtn.disabled = true;
        searchBtn.textContent = 'Searching...';

        const formData = new FormData();
        formData.append('audio', query);

        fetch('/search', { method: 'POST', body: formData })
            .then(res => res.json())
            .then(data => {
                if (data.error) throw new Error(data.error);

                // Load YouTube Embed
                currentWatchUrl = data.watch_url;
                youtubeEmbed.src = `https://www.youtube.com/embed/${data.video_id}`;
                videoContainer.classList.remove('d-none');
                downloadControls.classList.remove('d-none');
            })
            .catch(err => alert(err.message))
            .finally(() => {
                searchBtn.disabled = false;
                searchBtn.textContent = 'Search';
            });
    });

    // Phase 2: Process Download
    downloadForm.addEventListener('submit', (e) => {
        e.preventDefault();
        if (!currentWatchUrl) return;

        hideProgressBar();
        startFakeProgress();
        downloadBtn.disabled = true;
        btnText.textContent = 'Processing Media...';
        btnSpinner.classList.remove('d-none');

        const formData = new FormData(downloadForm);
        formData.append('watch_url', currentWatchUrl);

        fetch('/process_download', { method: 'POST', body: formData })
            .then(res => {
                if (!res.ok) {
                    return res.json().then(err => { throw new Error(err.error || 'Download failed.'); });
                }
                return res.json();
            })
            .then(data => {
                window.location.href = data.download_url;
                stopFakeProgress(true);
            })
            .catch(err => {
                console.error(err);
                stopFakeProgress(false);
                alert(`Error: ${err.message}`);
            });
    });

    function hideProgressBar() {
        clearInterval(fIntervals);
        progressBarContainer.classList.add('d-none');
        progressBar.style.width = '0%';
        progressBar.textContent = '';
        progressBar.classList.remove('bg-success');
    }

    function startFakeProgress() {
        let value = 0;
        progressBarContainer.classList.remove('d-none');
        fIntervals = setInterval(() => {
            if (value < 90) {
                value += Math.floor(Math.random() * 4) + 1;
                if (value > 90) value = 90;
                updateProgress(value);
            }
        }, 400);
    }

    function stopFakeProgress(success) {
        clearInterval(fIntervals);
        if (success) {
            updateProgress(100);
            progressBar.classList.add('bg-success');
            btnText.textContent = 'Download Started!';
            btnSpinner.classList.add('d-none');

            setTimeout(() => {
                btnText.textContent = 'Download';
                downloadBtn.disabled = false;
                hideProgressBar();
            }, 3000);
        } else {
            hideProgressBar();
            btnText.textContent = 'Download';
            btnSpinner.classList.add('d-none');
            downloadBtn.disabled = false;
        }
    }

    function updateProgress(value) {
        progressBar.style.width = value + '%';
        progressBar.textContent = value + '%';
    }
});