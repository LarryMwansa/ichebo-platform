/**
 * LearnVideoUpload — chunked video upload for the lesson-authoring form.
 *
 * Talks directly to the Go Video Engine on video.ichebo.org (not proxied
 * through Django) for the chunk PUTs themselves — Django's MEDIA_ENGINE_URL
 * setting is rendered into the page once globally (see author_lesson_form.html)
 * since this is browser-side JS, not a Django view, and has no settings access.
 *
 * Supports multiple instances on one page (desktop + mobile blocks both
 * render this widget — see _video_upload.html's mount_suffix comment),
 * keyed by suffix the same way EditorialUI is.
 */
const LearnVideoUpload = {
    CHUNK_POLL_INTERVAL_MS: 2000,
    _instances: {},

    _state(sfx) {
        sfx = sfx || '';
        if (!this._instances[sfx]) {
            this._instances[sfx] = { uploading: false };
        }
        return this._instances[sfx];
    },

    init(sfx) {
        sfx = sfx || '';
        const fileInput = document.getElementById('video-upload-file' + sfx);
        const replaceBtn = document.getElementById('video-upload-replace' + sfx);
        if (!fileInput) return;

        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) this._startUpload(sfx, file);
        });

        if (replaceBtn) {
            replaceBtn.addEventListener('click', () => {
                document.getElementById('video-upload-done' + sfx).style.display = 'none';
                document.getElementById('video-upload-idle' + sfx).style.display = 'block';
                document.getElementById('video-upload-url' + sfx).value = '';
            });
        }
    },

    _engineUrl() {
        return window.ICHEBO_MEDIA_ENGINE_URL || 'https://video.ichebo.org';
    },

    _csrfToken() {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? match[1] : '';
    },

    _showError(sfx, msg) {
        const el = document.getElementById('video-upload-error' + sfx);
        if (el) { el.textContent = msg; el.style.display = 'block'; }
        document.getElementById('video-upload-progress' + sfx).style.display = 'none';
        document.getElementById('video-upload-idle' + sfx).style.display = 'block';
    },

    _setProgress(sfx, pct, statusText) {
        document.getElementById('video-upload-pct' + sfx).textContent = Math.round(pct) + '%';
        document.getElementById('video-upload-bar' + sfx).style.width = Math.round(pct) + '%';
        if (statusText) document.getElementById('video-upload-status' + sfx).textContent = statusText;
    },

    async _startUpload(sfx, file) {
        const st = this._state(sfx);
        if (st.uploading) return;
        st.uploading = true;

        document.getElementById('video-upload-error' + sfx).style.display = 'none';
        document.getElementById('video-upload-idle' + sfx).style.display = 'none';
        document.getElementById('video-upload-progress' + sfx).style.display = 'block';
        this._setProgress(sfx, 0, 'Preparing upload…');

        try {
            // 1. Init — Django creates the media Record and forwards to the engine.
            const titleInput = document.querySelector('input[name="title"]');
            const initResp = await fetch('/api/media/upload/init/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this._csrfToken() },
                credentials: 'same-origin',
                body: JSON.stringify({
                    title: (titleInput && titleInput.value.trim()) || file.name,
                    filename: file.name,
                    file_size_bytes: file.size,
                    content_type: file.type || 'video/mp4',
                }),
            });
            if (!initResp.ok) throw new Error((await initResp.json()).error || 'Upload init failed');
            const init = await initResp.json();

            // 2. Chunk PUTs — straight to the Go engine, not through Django
            // (see this file's header comment).
            const totalChunks = init.total_chunks;
            const chunkSize = init.chunk_size_bytes;
            const checksums = [];
            for (let n = 0; n < totalChunks; n++) {
                const start = n * chunkSize;
                const end = Math.min(start + chunkSize, file.size);
                const chunk = file.slice(start, end);

                const chunkResp = await fetch(
                    `${this._engineUrl()}/engine/upload/${init.upload_id}/chunk/${n}`,
                    { method: 'PUT', body: chunk },
                );
                if (!chunkResp.ok) throw new Error(`Chunk ${n + 1}/${totalChunks} failed to upload`);
                const chunkData = await chunkResp.json();
                checksums.push({ n, checksum: chunkData.checksum });

                this._setProgress(sfx, ((n + 1) / totalChunks) * 70, `Uploading… (${n + 1}/${totalChunks})`);
            }

            // 3. Complete — Django assembles, submits the transcode job.
            this._setProgress(sfx, 75, 'Processing…');
            const completeResp = await fetch('/api/media/upload/complete/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this._csrfToken() },
                credentials: 'same-origin',
                body: JSON.stringify({
                    upload_id: init.upload_id,
                    record_id: init.record_id,
                    chunk_checksums: checksums,
                    quality_profiles: [], // empty = engine's own DefaultProfiles
                }),
            });
            if (!completeResp.ok) throw new Error((await completeResp.json()).error || 'Upload finalize failed');

            // 4. Poll the media Record until transcoding finishes.
            await this._pollUntilComplete(sfx, init.record_id, file.name);
        } catch (err) {
            this._showError(sfx, err.message || 'Upload failed — please try again.');
        } finally {
            st.uploading = false;
        }
    },

    async _pollUntilComplete(sfx, recordId, filename) {
        this._setProgress(sfx, 80, 'Transcoding…');
        // No fixed timeout — a long lecture-length video can legitimately
        // take longer than any short timeout would allow; the steward can
        // navigate away and the media Record keeps processing regardless,
        // they'd just need to come back and re-attach the result. Capped
        // at a generous number of polls so a genuinely stuck job doesn't
        // poll forever in an open tab.
        const maxPolls = 600; // 600 * 2s = 20 minutes
        for (let i = 0; i < maxPolls; i++) {
            await new Promise((r) => setTimeout(r, this.CHUNK_POLL_INTERVAL_MS));
            const resp = await fetch(`/api/media/videos/${recordId}/`, { credentials: 'same-origin' });
            if (!resp.ok) continue;
            const data = await resp.json();
            if (data.transcoding_status === 'complete' && data.video_url) {
                document.getElementById('video-upload-url' + sfx).value = data.video_url;
                document.getElementById('video-upload-progress' + sfx).style.display = 'none';
                document.getElementById('video-upload-filename' + sfx).textContent = filename;
                document.getElementById('video-upload-done' + sfx).style.display = 'flex';
                return;
            }
            if (data.transcoding_status === 'failed') {
                throw new Error('Video processing failed — please try a different file.');
            }
            this._setProgress(sfx, 80 + Math.min(i / 4, 15), 'Transcoding…');
        }
        throw new Error('Still processing after 20 minutes — refresh this page later to check status.');
    },
};
