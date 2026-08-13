let currentURL = "";

// 🔥 Get current tab URL
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  currentURL = tabs[0].url;
  document.getElementById("url").innerText = currentURL;
});

// 🎯 Color logic
function getColor(score) {
  if (score >= 80) return "green";
  if (score >= 50) return "orange";
  return "red";
}

// 🚀 Analyze button
document.getElementById("analyzeBtn").addEventListener("click", async () => {
  document.getElementById("analyzeBtn").innerText = "Analyzing...";

  try {
    const res = await fetch("http://127.0.0.1:8000/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url: currentURL }),
    });

    const data = await res.json();

    // Show result
    document.getElementById("result").classList.remove("hidden");

    const scoreCircle = document.getElementById("scoreCircle");
    scoreCircle.innerText = data.trust_score;
    scoreCircle.className = getColor(data.trust_score);

    document.getElementById("security").innerText = data.breakdown.security;
    document.getElementById("privacy").innerText = data.breakdown.privacy;
    document.getElementById("reviews").innerText = data.breakdown.reviews;

    // Tips
    const tipsDiv = document.getElementById("tips");
    tipsDiv.innerHTML = "<h4>Tips:</h4>";

    data.tips.forEach((tip) => {
      const p = document.createElement("p");
      p.innerText = tip;
      tipsDiv.appendChild(p);
    });

  } catch (err) {
    alert("Backend not running!");
  }

  document.getElementById("analyzeBtn").innerText = "Analyze";
});