<script>
  import { ProcessVideo } from '../wailsjs/go/main/App.js';
  import { main } from '../wailsjs/go/models.ts';
  
  let selectedVideoFile = null;
  let videoFileName = "No video selected";
  let isAnalyzing = false;
  let analysisResult = null;

  // Analysis parameters with default values
  let parameters = {
    // Threshold parameters
    threshold_high: 0.60,
    threshold_low: 0.35,
    hysteresis_margin: 0.05,
    
    // Timing parameters
    min_duration: 0.08,
    
    // Smoothing parameters
    smoothing_method: "ema",
    smoothing_alpha: 0.7,
    
    // Motion weights
    motion_weights: {
      displacement: 0.2,
      velocity: 0.25,
      acceleration: 0.2,
      direction_change: 0.15,
      pose_change: 0.2
    },
    
    // Advanced options
    enable_tame_tsume: false,
    save_keypoints: false
  };

  // Computed property for total weight
  $: totalWeight = Object.values(parameters.motion_weights).reduce((sum, weight) => sum + weight, 0);
  $: weightWarning = Math.abs(totalWeight - 1.0) > 0.01;

  function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
      selectedVideoFile = file;
      videoFileName = file.name;
    } else {
      selectedVideoFile = null;
      videoFileName = "No video selected";
    }
  }

  function resetToDefaults() {
    parameters = {
      threshold_high: 0.60,
      threshold_low: 0.35,
      hysteresis_margin: 0.05,
      min_duration: 0.08,
      smoothing_method: "ema",
      smoothing_alpha: 0.7,
      motion_weights: {
        displacement: 0.2,
        velocity: 0.25,
        acceleration: 0.2,
        direction_change: 0.15,
        pose_change: 0.2
      },
      enable_tame_tsume: false,
      save_keypoints: false
    };
  }

  async function runAnalysis() {
    if (!selectedVideoFile) {
      alert("Please select a video file first.");
      return;
    }

    isAnalyzing = true;
    analysisResult = null; // Clear previous results

    try {
      // Create output path based on input file
      const inputPath = selectedVideoFile.path || selectedVideoFile.name;
      const outputPath = inputPath.replace(/\.[^/.]+$/, "_processed.mp4");
      
      // Create the request object
      const request = new main.ProcessVideoRequest({
        input_path: inputPath,
        output_path: outputPath,
        config: JSON.stringify(parameters)
      });

      console.log("Starting analysis with parameters:", parameters);
      
      // Call the Go backend
      const response = await ProcessVideo(request);
      
      if (response.status === "success") {
        analysisResult = {
          status: "success",
          outputVideoPath: response.output_video_path,
          databaseId: response.database_id,
          message: response.message,
          inputPath: inputPath,
          analysisTime: new Date().toLocaleString()
        };
      } else {
        analysisResult = {
          status: "error",
          message: response.message,
          errorType: response.error_type
        };
      }
      
    } catch (error) {
      console.error("Error during analysis:", error);
      analysisResult = {
        status: "error",
        message: error.message || error.toString(),
        errorType: "UnexpectedError"
      };
    } finally {
      isAnalyzing = false;
    }
  }
</script>

<main>
  <h1>Frame Timing Analyzer</h1>

  <div class="card">
    <h2>1. Select Video</h2>
    <div class="input-box">
      <input type="file" id="video-input" accept="video/*" on:change={handleFileSelect} style="display: none;">
      <label for="video-input" class="btn">Choose File</label>
      <span class="file-name">{videoFileName}</span>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <h2>2. Analysis Parameters</h2>
      <button class="btn-secondary" on:click={resetToDefaults}>Reset to Defaults</button>
    </div>
    
    <!-- Motion Thresholds -->
    <fieldset>
      <legend>Motion Thresholds</legend>
      <div class="param-grid">
        <div class="param-item">
          <label for="threshold-high">High Threshold:</label>
          <input type="range" id="threshold-high" min="0.4" max="0.9" step="0.05" bind:value={parameters.threshold_high}>
          <span class="param-value">{parameters.threshold_high}</span>
        </div>
        <div class="param-item">
          <label for="threshold-low">Low Threshold:</label>
          <input type="range" id="threshold-low" min="0.1" max="0.6" step="0.05" bind:value={parameters.threshold_low}>
          <span class="param-value">{parameters.threshold_low}</span>
        </div>
        <div class="param-item">
          <label for="hysteresis-margin">Hysteresis Margin:</label>
          <input type="range" id="hysteresis-margin" min="0.01" max="0.15" step="0.01" bind:value={parameters.hysteresis_margin}>
          <span class="param-value">{parameters.hysteresis_margin}</span>
        </div>
      </div>
    </fieldset>

    <!-- Timing Settings -->
    <fieldset>
      <legend>Timing Settings</legend>
      <div class="param-grid">
        <div class="param-item">
          <label for="min-duration">Min Duration (s):</label>
          <input type="range" id="min-duration" min="0.02" max="0.2" step="0.01" bind:value={parameters.min_duration}>
          <span class="param-value">{parameters.min_duration}</span>
        </div>
        <div class="param-item">
          <label for="smoothing-method">Smoothing Method:</label>
          <select id="smoothing-method" bind:value={parameters.smoothing_method}>
            <option value="ema">Exponential Moving Average</option>
            <option value="window">Window Average</option>
          </select>
        </div>
        <div class="param-item">
          <label for="smoothing-alpha">Smoothing Alpha:</label>
          <input type="range" id="smoothing-alpha" min="0.1" max="1.0" step="0.1" bind:value={parameters.smoothing_alpha}>
          <span class="param-value">{parameters.smoothing_alpha}</span>
        </div>
      </div>
    </fieldset>

    <!-- Motion Weights -->
    <fieldset>
      <legend>Motion Component Weights</legend>
      <div class="param-grid">
        <div class="param-item">
          <label for="weight-displacement">Displacement:</label>
          <input type="range" id="weight-displacement" min="0.0" max="0.5" step="0.05" bind:value={parameters.motion_weights.displacement}>
          <span class="param-value">{parameters.motion_weights.displacement}</span>
        </div>
        <div class="param-item">
          <label for="weight-velocity">Velocity:</label>
          <input type="range" id="weight-velocity" min="0.0" max="0.5" step="0.05" bind:value={parameters.motion_weights.velocity}>
          <span class="param-value">{parameters.motion_weights.velocity}</span>
        </div>
        <div class="param-item">
          <label for="weight-acceleration">Acceleration:</label>
          <input type="range" id="weight-acceleration" min="0.0" max="0.5" step="0.05" bind:value={parameters.motion_weights.acceleration}>
          <span class="param-value">{parameters.motion_weights.acceleration}</span>
        </div>
        <div class="param-item">
          <label for="weight-direction">Direction Change:</label>
          <input type="range" id="weight-direction" min="0.0" max="0.5" step="0.05" bind:value={parameters.motion_weights.direction_change}>
          <span class="param-value">{parameters.motion_weights.direction_change}</span>
        </div>
        <div class="param-item">
          <label for="weight-pose">Pose Change:</label>
          <input type="range" id="weight-pose" min="0.0" max="0.5" step="0.05" bind:value={parameters.motion_weights.pose_change}>
          <span class="param-value">{parameters.motion_weights.pose_change}</span>
        </div>
      </div>
      <div class="weight-total {weightWarning ? 'warning' : ''}">
        Total Weight: {totalWeight.toFixed(2)} {weightWarning ? '⚠️ Should be 1.0' : '✓'}
      </div>
    </fieldset>

    <!-- Advanced Options -->
    <fieldset>
      <legend>Advanced Options</legend>
      <div class="param-grid">
        <div class="param-item checkbox-item">
          <label for="enable-tame-tsume">
            <input type="checkbox" id="enable-tame-tsume" bind:checked={parameters.enable_tame_tsume}>
            Enable Tame/Tsume Detection
          </label>
        </div>
        <div class="param-item checkbox-item">
          <label for="save-keypoints">
            <input type="checkbox" id="save-keypoints" bind:checked={parameters.save_keypoints}>
            Save Keypoints Data
          </label>
        </div>
      </div>
    </fieldset>
  </div>

  <div class="card">
    <h2>3. Run</h2>
    <button class="btn run-btn" on:click={runAnalysis} disabled={isAnalyzing}>
      {isAnalyzing ? 'Analyzing...' : 'Run Analysis'}
    </button>
  </div>

  <!-- Results Display Area -->
  {#if analysisResult}
    <div class="card results-card">
      <h2>4. Results</h2>
      
      {#if analysisResult.status === "success"}
        <div class="results-success">
          <div class="result-header">
            <span class="status-badge success">✓ Analysis Complete</span>
            <span class="analysis-time">{analysisResult.analysisTime}</span>
          </div>
          
          <div class="result-details">
            <div class="result-item">
              <label>Input Video:</label>
              <span class="file-path">{analysisResult.inputPath}</span>
            </div>
            
            <div class="result-item">
              <label>Output Video:</label>
              <span class="file-path">{analysisResult.outputVideoPath}</span>
              <button class="btn-small" on:click={() => navigator.clipboard.writeText(analysisResult.outputVideoPath)}>
                Copy Path
              </button>
            </div>
            
            {#if analysisResult.databaseId}
              <div class="result-item">
                <label>Database ID:</label>
                <span class="database-id">{analysisResult.databaseId}</span>
              </div>
            {/if}
            
            <div class="result-item">
              <label>Status:</label>
              <span class="success-message">{analysisResult.message}</span>
            </div>
          </div>
          
          <div class="result-actions">
            <button class="btn" on:click={() => analysisResult = null}>
              Clear Results
            </button>
          </div>
        </div>
      {:else}
        <div class="results-error">
          <div class="result-header">
            <span class="status-badge error">✗ Analysis Failed</span>
            <span class="analysis-time">{new Date().toLocaleString()}</span>
          </div>
          
          <div class="result-details">
            {#if analysisResult.errorType}
              <div class="result-item">
                <label>Error Type:</label>
                <span class="error-type">{analysisResult.errorType}</span>
              </div>
            {/if}
            
            <div class="result-item">
              <label>Error Message:</label>
              <span class="error-message">{analysisResult.message}</span>
            </div>
          </div>
          
          <div class="result-actions">
            <button class="btn" on:click={() => analysisResult = null}>
              Clear Results
            </button>
          </div>
        </div>
      {/if}
    </div>
  {/if}

  <!-- Loading Modal Overlay -->
  {#if isAnalyzing}
    <div class="modal-overlay">
      <div class="modal-content">
        <div class="spinner"></div>
        <h3>Processing Video</h3>
        <p>Analyzing frames and applying timing adjustments...</p>
        <p class="modal-note">This may take several minutes depending on video length.</p>
      </div>
    </div>
  {/if}

</main>

<style>
  :root {
    --primary-color: #4a86e8;
    --background-color: #f0f2f5;
    --card-background: #ffffff;
    --text-color: #333;
    --border-radius: 8px;
  }

  main {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    text-align: center;
    padding: 2em;
    background-color: var(--background-color);
    color: var(--text-color);
  }

  h1 {
    color: var(--primary-color);
  }

  .card {
    background-color: var(--card-background);
    border-radius: var(--border-radius);
    padding: 1.5em;
    margin: 1.5rem auto;
    max-width: 600px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  }

  .input-box {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1em;
  }

  .btn {
    padding: 10px 20px;
    border: none;
    border-radius: 5px;
    background-color: var(--primary-color);
    color: white;
    cursor: pointer;
    font-size: 1em;
    transition: background-color 0.2s;
  }

  .btn:hover {
    background-color: #357ae8;
  }

  .file-name {
    background-color: #f0f2f5;
    padding: 10px;
    border-radius: 5px;
    min-width: 200px;
    text-align: left;
  }

  fieldset {
    border: 1px solid #ccc;
    border-radius: var(--border-radius);
    padding: 1em;
  }

  .run-btn {
    width: 100%;
    font-size: 1.2em;
    padding: 15px;
  }

  .param-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1em;
    margin-top: 1em;
  }

  .param-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1em;
  }

  .param-item label {
    font-weight: 500;
    min-width: 140px;
    text-align: left;
  }

  .param-item input[type="range"] {
    flex: 1;
    margin: 0 10px;
  }

  .param-item select {
    flex: 1;
    padding: 5px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background-color: white;
  }

  .param-value {
    min-width: 50px;
    text-align: right;
    font-family: monospace;
    background-color: #f8f9fa;
    padding: 4px 8px;
    border-radius: 4px;
    border: 1px solid #e9ecef;
  }

  .checkbox-item {
    justify-content: flex-start;
  }

  .checkbox-item label {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: auto;
  }

  .checkbox-item input[type="checkbox"] {
    margin: 0;
  }

  fieldset {
    margin-bottom: 1.5em;
  }

  legend {
    font-weight: 600;
    color: var(--primary-color);
    padding: 0 10px;
  }

  .weight-total {
    margin-top: 1em;
    padding: 8px 12px;
    background-color: #e8f5e8;
    border: 1px solid #4caf50;
    border-radius: 4px;
    text-align: center;
    font-weight: 500;
  }

  .weight-total.warning {
    background-color: #fff3cd;
    border-color: #ffc107;
    color: #856404;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1em;
  }

  .card-header h2 {
    margin: 0;
  }

  .btn-secondary {
    padding: 8px 16px;
    border: 1px solid #6c757d;
    border-radius: 4px;
    background-color: #6c757d;
    color: white;
    cursor: pointer;
    font-size: 0.9em;
    transition: background-color 0.2s;
  }

  .btn-secondary:hover {
    background-color: #5a6268;
  }

  @media (min-width: 768px) {
    .param-grid {
      grid-template-columns: 1fr 1fr;
    }
  }

  /* Modal Loading Overlay */
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    backdrop-filter: blur(2px);
  }

  .modal-content {
    background-color: var(--card-background);
    border-radius: var(--border-radius);
    padding: 2em;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    max-width: 400px;
    width: 90%;
  }

  .modal-content h3 {
    color: var(--primary-color);
    margin: 1em 0 0.5em 0;
  }

  .modal-content p {
    margin: 0.5em 0;
    color: var(--text-color);
  }

  .modal-note {
    font-size: 0.9em;
    color: #666;
    font-style: italic;
  }

  /* Spinner Animation */
  .spinner {
    width: 50px;
    height: 50px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid var(--primary-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 1em auto;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  /* Disabled button state */
  .btn:disabled {
    background-color: #ccc;
    cursor: not-allowed;
    opacity: 0.6;
  }

  .btn:disabled:hover {
    background-color: #ccc;
  }

  /* Results Display Styles */
  .results-card {
    border-left: 4px solid var(--primary-color);
  }

  .results-success {
    background-color: #f8fff8;
    border: 1px solid #d4edda;
    border-radius: var(--border-radius);
    padding: 1em;
  }

  .results-error {
    background-color: #fff8f8;
    border: 1px solid #f5c6cb;
    border-radius: var(--border-radius);
    padding: 1em;
  }

  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1em;
    padding-bottom: 0.5em;
    border-bottom: 1px solid #e9ecef;
  }

  .status-badge {
    padding: 6px 12px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.9em;
  }

  .status-badge.success {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
  }

  .status-badge.error {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
  }

  .analysis-time {
    font-size: 0.85em;
    color: #6c757d;
    font-style: italic;
  }

  .result-details {
    margin: 1em 0;
  }

  .result-item {
    display: flex;
    align-items: center;
    margin-bottom: 0.75em;
    gap: 1em;
  }

  .result-item label {
    font-weight: 600;
    min-width: 120px;
    color: var(--text-color);
  }

  .file-path {
    font-family: monospace;
    background-color: #f8f9fa;
    padding: 4px 8px;
    border-radius: 4px;
    border: 1px solid #e9ecef;
    flex: 1;
    word-break: break-all;
    font-size: 0.9em;
  }

  .database-id {
    font-family: monospace;
    background-color: #e3f2fd;
    color: #1565c0;
    padding: 4px 8px;
    border-radius: 4px;
    border: 1px solid #bbdefb;
    font-weight: 600;
  }

  .success-message {
    color: #155724;
    font-weight: 500;
  }

  .error-type {
    font-family: monospace;
    background-color: #fff3cd;
    color: #856404;
    padding: 4px 8px;
    border-radius: 4px;
    border: 1px solid #ffeaa7;
    font-weight: 600;
  }

  .error-message {
    color: #721c24;
    font-weight: 500;
    flex: 1;
  }

  .btn-small {
    padding: 4px 8px;
    font-size: 0.8em;
    background-color: #6c757d;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
  }

  .btn-small:hover {
    background-color: #5a6268;
  }

  .result-actions {
    margin-top: 1em;
    padding-top: 1em;
    border-top: 1px solid #e9ecef;
    text-align: center;
  }

  @media (max-width: 768px) {
    .result-item {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5em;
    }

    .result-item label {
      min-width: auto;
    }

    .file-path {
      width: 100%;
    }

    .result-header {
      flex-direction: column;
      gap: 0.5em;
      align-items: flex-start;
    }
  }

</style>