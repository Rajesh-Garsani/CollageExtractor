/**
 * Asynchronous Core Frontend Client Controller for Collage Extractor.
 * Acts as the central orchestrator, delegating DOM and Chat logic
 * to imported ES6 modules.
 */

import { UIManager } from './ui.js';
import { ChatInterface } from './chat.js';

class CollageExtractorApp {
    constructor() {
        // State
        this.activeSessionId = null;
        this.activeCollageId = null;
        this.detectedPanels = [];

        // Instantiate Modules
        this.ui = new UIManager();
        this.chat = new ChatInterface();

        this.initController();
    }

    initController() {
        // Bind UI Upload Events to our local upload handler
        this.ui.bindUploadEvents((file) => this.handleFileUpload(file));

        // Bind Chat Submit Events to our local chat handler
        this.chat.bindChatEvents((text) => this.executeChatExtraction(text));

        // Bind Global Reset Button
        this.ui.resetBtn.addEventListener('click', () => this.resetWorkspaceState());
    }

    async handleFileUpload(file) {
        const formData = new FormData();
        formData.append('image', file);

        this.ui.setUploadProgress(0);

        try {
            // Context Pass 1: Submit Binary Multi-part Payload
            const response = await fetch('/api/v1/upload/', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error("Upload constraints violated.");
            const data = await response.json();

            this.activeSessionId = data.session_id;
            this.activeCollageId = data.id;

            // UI Updates
            this.ui.updateSessionBadge(this.activeSessionId);
            this.ui.setWorkspaceStage('analysis');

            // Progress to Segment Identification
            this.triggerCollageAnalysis(data.image);

        } catch (error) {
            this.ui.showToast(error.message, true);
            this.ui.setWorkspaceStage('upload');
            this.ui.progressBarContainer.classList.add('d-none');
        }
    }

    async triggerCollageAnalysis(imageUrl) {
        try {
            // Context Pass 2: Asynchronous computer vision analysis loop
            const response = await fetch(`/api/v1/analyze/${this.activeCollageId}/`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error("Computer Vision Analysis failed.");
            const data = await response.json();

            this.detectedPanels = data.panels;

            // Delegate Canvas Rendering to UI Manager
            this.ui.renderCanvas(imageUrl, this.detectedPanels);
            this.ui.setWorkspaceStage('canvas');

            // Open console communication channels via Chat Manager
            this.chat.setLoadingState(false);
            this.chat.appendMessage("Analysis complete. Panel structural coordinates mapped. Systems fully armed for extraction commands.", "system");

        } catch (error) {
            this.ui.showToast(error.message, true);
            this.ui.setWorkspaceStage('upload');
        }
    }

    async executeChatExtraction(promptText) {
        // Lock UI State
        this.chat.setLoadingState(true);

        try {
            // Context Pass 3: Process the natural language instruction
            const response = await fetch('/api/v1/chat/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.activeSessionId,
                    prompt: promptText
                })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "Failed to execute pipeline transformation step.");

            const opsApplied = data.applied_operations.join(', ');

            // Render High-End Image Output via Chat Manager
            this.chat.appendMessage(
                `Success! Extracted image pipeline execution completed in ${data.processing_time_ms}ms. Operations performed: [${opsApplied}].`,
                'system',
                data.result_image
            );

        } catch (error) {
            this.chat.appendMessage(`Error: ${error.message}`, 'system');
            this.ui.showToast(error.message, true);
        } finally {
            // Unlock UI State
            this.chat.setLoadingState(false);
        }
    }

    resetWorkspaceState() {
        this.activeSessionId = null;
        this.activeCollageId = null;
        this.detectedPanels = [];

        // Reset Modules
        this.ui.clearCanvas();
        this.ui.updateSessionBadge(null);
        this.ui.setWorkspaceStage('upload');
        this.chat.reset();

        this.ui.showToast("Session instances purged successfully.");
    }
}

// Instantiate App
document.addEventListener('DOMContentLoaded', () => {
    window.AppEngine = new CollageExtractorApp();
});