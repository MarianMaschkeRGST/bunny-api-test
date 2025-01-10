// https://github.com/embedly/player.js#playerjs
// Initialize player function that can be called by both DOMContentLoaded and HTMX
 function initializePlayer() {
  const iframe = document.getElementById("bunny-stream-embed");
  
  iframe.onload = () => {
    // Create a PlayerJS instance
    const player = new playerjs.Player(iframe, {
      origin: "https://iframe.mediadelivery.net"
    });


    console.log("Player initialized", player);

    // Add error handling
    player.on('error', (error) => {
      console.error('Player error:', error);
    });

    let totalDuration = 0;

    // Ready event handler
    player.on("ready", () => {
      console.log("Player ready");

      player.getDuration((duration) => {
        totalDuration = duration;
        console.log(`Video duration: ${duration}s`);
      });
    });

    // Play event handler
    player.on("play", () => {
      console.log("Video is playing");
    });

    // Play button event listener
    document.getElementById("play").addEventListener("click", () => {
      player.play();
    });

    // Pause button event listener
    document.getElementById("pause").addEventListener("click", () => {
      player.pause();
    });

    // Timeupdate event handler
    player.on("timeupdate", (timingData) => {
      const currentTime = timingData.seconds;
      const progressPercentage = (currentTime / timingData.duration) * 100;

      const progressText = document.querySelector(".progress-text");
      if (progressText) {
        progressText.textContent = `${Math.floor(progressPercentage)}%`;
      }

      const progressBar = document.querySelector(".progress");
      if (progressBar) {
        progressBar.style.width = `${Math.floor(progressPercentage)}%`;
      }

      if (Math.floor(progressPercentage) >= 100) {
        alert("Video completed");
      }
    });
  };
}

htmx.onLoad(function(content) {
  if (content.querySelector("#bunny-stream-embed")) {
    initializePlayer();
  }
});