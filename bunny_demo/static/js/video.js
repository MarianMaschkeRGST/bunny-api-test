//Manage video progress for submission and initial settings

let currentProgress = 0;

function getCurrentProgress() {
  console.log("getCurrentProgress called, returning:", currentProgress);
  return Math.floor(currentProgress);
}

function initializePlayer() {
  const iframe = document.getElementById("bunny-stream-embed");

  iframe.onload = () => {
    const player = new playerjs.Player(iframe, {
      origin: "https://iframe.mediadelivery.net",
    });

    player.on("error", (error) => {
      console.error("Player error:", error);
    });

    player.on("ready", () => {
      console.log("Player ready");
      // Duration logic is not working
      // player.getDuration((duration) => {
      //   totalDuration = duration;
      //   console.log(`Video duration: ${duration}s`);
      // });
    });

    player.on("play", () => {
      console.log("Video is playing");
    });

    document.getElementById("play").addEventListener("click", () => {
      player.play();
    });

    document.getElementById("pause").addEventListener("click", () => {
      player.pause();
      console.log(currentProgress);
    });

    player.on("timeupdate", (timingData) => {
      if (timingData.duration > 0) {
        const currentTime = timingData.seconds;
        const progressPercentage = (currentTime / timingData.duration) * 100;
        currentProgress = progressPercentage;

        const progressText = document.querySelector(".progress-text");
        if (progressText) {
          progressText.textContent = `${Math.floor(progressPercentage)}%`;
        }

        const progressBar = document.querySelector(".progress");
        if (progressBar) {
          progressBar.style.width = `${Math.floor(progressPercentage)}%`;
        }

        // Update progress input value
        const progressInput = document.getElementById("progress-input");
        if (progressInput) {
          progressInput.value = Math.floor(currentProgress);
        }

        if (Math.floor(progressPercentage) >= 100) {
          alert("Video completed");
        }
      }
    });
  };
}

document.body.addEventListener("htmx:beforeRequest", function (evt) {
  const form = evt.detail.elt;
  if (form.id === "progress-form") {
    const progressInput = document.getElementById("progress-input");
    if (progressInput) {
      progressInput.value = Math.floor(currentProgress);
    }
    console.log("About to send watch_progress update. Value:", progressInput?.value);
  }
});

document.body.addEventListener("htmx:afterRequest", function (evt) {
  const form = evt.detail.elt;
  if (form.id === "progress-form") {
    if (evt.detail.successful) {
      console.log("Progress saved successfully. Response:", evt.detail.xhr.responseText);
    } else {
      console.error("Failed to save progress:", evt.detail.xhr.responseText);
    }
  }
});

htmx.onLoad(function (content) {
  if (content.querySelector("#bunny-stream-embed")) {
    initializePlayer();
  }
});
