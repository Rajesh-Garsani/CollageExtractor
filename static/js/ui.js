export class UIManager {
    constructor() {
        // Core Stage Containers
        this.uploadStage = document.getElementById('uploadStageContainer');
        this.analysisStage = document.getElementById('analysisStageContainer');
        this.canvasStage = document.getElementById('canvasStageContainer');

        // Upload Elements
        this.dropzone = document.getElementById('dropzone');
        this.fileInput = document.getElementById('fileInput');
        this.progressBarContainer = document.getElementById('uploadProgressBarContainer');
        this.progressBar = document.getElementById('uploadProgressBar');

        // Canvas Elements
        this.canvas = document.getElementById('visualizationCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.detectedCountLabel = document.getElementById('detectedCountLabel');
        this.sessionBadge = document.getElementById('sessionBadge');
        this.resetBtn = document.getElementById('resetSessionBtn');

        // State variables
        this.sourceImageElement = new Image();
    }

    /**
     * Binds Drag and Drop events to the provided callback.
     * @param {Function} onFileDrop - Callback executed when a valid file is dropped.
     */
    bindUploadEvents(onFileDrop) {
        ['dragenter', 'dragover'].forEach(eventName => {
            this.dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                this.dropzone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            this.dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                this.dropzone.classList.remove('dragover');
            }, false);
        });

        this.dropzone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) onFileDrop(files[0]);
        });

        this.fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) onFileDrop(e.target.files[0]);
        });
    }

    /**
     * Switches the active workspace view.
     * @param {string} stage - 'upload', 'analysis', or 'canvas'
     */
    setWorkspaceStage(stage) {
        this.uploadStage.classList.add('d-none');
        this.analysisStage.classList.add('d-none');
        this.canvasStage.classList.add('d-none');

        if (stage === 'upload') this.uploadStage.classList.remove('d-none');
        if (stage === 'analysis') this.analysisStage.classList.remove('d-none');
        if (stage === 'canvas') this.canvasStage.classList.remove('d-none');
    }

    /**
     * Triggers a globally scoped Bootstrap Toast notification.
     * @param {string} message - The text to display.
     * @param {boolean} isError - Changes color theme (red for error, green for success).
     */
    showToast(message, isError = false) {
        const toastEl = document.getElementById('systemToast');
        const msgEl = document.getElementById('toastMessage');

        msgEl.innerText = message;
        toastEl.classList.remove('bg-dark', 'bg-danger', 'bg-success');
        toastEl.classList.add(isError ? 'bg-danger' : 'bg-success');

        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    }

    updateSessionBadge(sessionId) {
        if (sessionId) {
            this.sessionBadge.innerText = `Session: ${sessionId.substring(0, 8)}`;
            this.sessionBadge.classList.replace('bg-secondary', 'bg-primary');
        } else {
            this.sessionBadge.innerText = "No Active Session";
            this.sessionBadge.classList.replace('bg-primary', 'bg-secondary');
        }
    }

    setUploadProgress(percentage) {
        this.progressBarContainer.classList.remove('d-none');
        this.progressBar.style.width = `${percentage}%`;
    }

    /**
     * Renders the source image and overlays detected bounding boxes via Canvas API.
     * @param {string} imageUrl - Blob or server URL of the image.
     * @param {Array} panels - Array of panel objects containing coordinates.
     */
   /**
     * Renders the source image and overlays detected bounding boxes via Canvas API.
     */
    renderCanvas(imageUrl, panels) {
        this.detectedCountLabel.innerText = `${panels.length} Image Panels Isolated`;
        this.sourceImageElement.src = imageUrl;

        this.sourceImageElement.onload = () => {
            this.canvas.width = this.sourceImageElement.naturalWidth;
            this.canvas.height = this.sourceImageElement.naturalHeight;

            // 1. Draw Base Image
            this.ctx.drawImage(this.sourceImageElement, 0, 0);

            // 2. Draw High-Tech Vector Overlays
            panels.forEach(panel => {
                // Dynamic styling based on image resolution
                const lineWidth = Math.max(3, Math.floor(this.canvas.width / 600));

                // Draw Box
                this.ctx.lineWidth = lineWidth;
                this.ctx.strokeStyle = '#6366f1'; // Indigo accent
                this.ctx.strokeRect(panel.x_coord, panel.y_coord, panel.width, panel.height);

                // 3. Smart Text Labeling (Pill Badges)
                let displayTag = panel.ocr_data && panel.ocr_data.image_number ?
                                 `No. ${panel.ocr_data.image_number}` :
                                 `ID: ${panel.panel_index}`;

                // Dynamic Font Sizing (Limits to keep it readable but not massive)
                const fontSize = Math.min(Math.max(16, Math.floor(panel.width * 0.08)), 24);
                this.ctx.font = `bold ${fontSize}px system-ui, sans-serif`;

                const textMetrics = this.ctx.measureText(displayTag);
                const textWidth = textMetrics.width;
                const padX = 10;
                const padY = 8;
                const badgeHeight = fontSize + (padY * 2);

                // Shadow for readability over complex comic art
                this.ctx.shadowColor = 'rgba(0, 0, 0, 0.6)';
                this.ctx.shadowBlur = 6;
                this.ctx.shadowOffsetX = 2;
                this.ctx.shadowOffsetY = 2;

                // Draw Badge Background (Dark Indigo)
                this.ctx.fillStyle = 'rgba(30, 33, 54, 0.95)';
                this.ctx.beginPath();
                this.ctx.roundRect(
                    panel.x_coord + lineWidth,
                    panel.y_coord + lineWidth,
                    textWidth + (padX * 2),
                    badgeHeight,
                    [0, 0, 8, 0] // Round bottom-right corner only
                );
                this.ctx.fill();

                // Draw Text
                this.ctx.shadowBlur = 0; // Turn off shadow for crisp text
                this.ctx.shadowOffsetX = 0;
                this.ctx.shadowOffsetY = 0;
                this.ctx.fillStyle = '#ffffff';
                this.ctx.fillText(
                    displayTag,
                    panel.x_coord + lineWidth + padX,
                    panel.y_coord + lineWidth + fontSize + (padY / 2)
                );
            });
        };
    }
    clearCanvas() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.setUploadProgress(0);
        this.progressBarContainer.classList.add('d-none');
    }
}