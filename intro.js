document.addEventListener("DOMContentLoaded", () => {
  const overlay = document.getElementById("introOverlay");

  // Hide intro after delay
  setTimeout(() => {
    overlay.style.transition = "opacity 1s ease";
    overlay.style.opacity = "0";

    setTimeout(() => {
      overlay.style.display = "none";
    }, 1000);

  }, 2500); // 2.5 seconds intro
});
