// Create a PlayerJS instance with the 'bunny-stream-embed' element
const player = new playerjs.Player("bunny-stream-embed");

// Initialize variables to store total duration and last progress point
let totalDuration = 0;
let lastProgress = 0;

// Event handler when the player is ready
player.on("ready", () => {
  console.log("Ready");
});
player.on("play", () => {
  console.log("playing");
});

// Event handler when the video is played
player.on("play", () => {
  console.log("Video is playing");
});
// Event listener for the 'play' button
document.getElementById("play").addEventListener("click", () => {
  player.play();
});

// Event listener for the 'pause' button
document.getElementById("pause").addEventListener("click", () => {
  player.pause();
});

// Get the total duration of the video and start playing
player.getDuration((duration) => {
  totalDuration = duration;
});

// Event handler for time updates when the player is playing
player.on("timeupdate", (timingData) => {
  // Get current seconds
  const currentTime = timingData.seconds;

  // Calculate progress percentage and round to the nearest 25%
  const progressPercentage = (currentTime / timingData.duration) * 100;
  const progressRounded = Math.floor(progressPercentage / 25) * 25;

  // Log the progress percentage
  console.log("Progress Percentage: " + Math.floor(progressPercentage) + "%");

  // Update the progress text on the page
  const progressText = document.querySelector(".progress-text");
  progressText.textContent = `${Math.floor(progressPercentage)}%`;

  const progressBar = document.querySelector(".progress");
  progressBar.style.width = `${Math.floor(progressPercentage)}%`;

  //   // Check if progress reached a new 25% milestone and update the progress bar
  //   if (progressRounded > lastProgress) {
  //     console.log(`Video progress: ${progressRounded}%`);
  //     lastProgress = progressRounded;

  //     // Update the progress bar width on the page
  //     const progressBar = document.querySelector(".progress");
  //     progressBar.style.width = `${progressRounded}%`;
  //   }
  if ((progressPercentage = 100)) {
    alert("動画終了");
  }
});
