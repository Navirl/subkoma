<script>
  let selectedVideoFile = null;
  let videoFileName = "No video selected";

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

  function runAnalysis() {
    if (!selectedVideoFile) {
      alert("Please select a video file first.");
      return;
    }
    // TODO: Call Go backend function
    console.log(`Starting analysis for: ${selectedVideoFile.name}`);
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
    <h2>2. Analysis Parameters</h2>
    <fieldset>
      <legend>Controls</legend>
      <!-- Parameter controls will go here in a future task -->
      <p style="text-align: center; color: #888;">Parameter controls will be added in a future task.</p>
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

</style>