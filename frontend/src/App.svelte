<script>
  import { ProcessVideo } from '../wailsjs/go/main/App.js';
  import { main } from '../wailsjs/go/models.ts';
  
  let selectedVideoFile = null;
  let videoFileName = "No video selected";

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
        alert(`Analysis completed successfully!\nOutput: ${response.output_video_path}`);
      } else {
        alert(`Analysis failed: ${response.message}`);
      }
      
    } catch (error) {
      console.error("Error during analysis:", error);
      alert(`Error: ${error.message || error}`);
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
    <button class="btn run-btn" on:click={runAnalysis}>Run Analysis</button>
  </div>

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

</style>