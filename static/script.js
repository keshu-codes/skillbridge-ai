// SkillBridge AI - Universal Career Analyzer
// static/script.js

document.addEventListener("DOMContentLoaded", function () {
  console.log("SkillBridge AI - Universal Career Analyzer loaded");

  // Initialize file upload
  initFileUpload();

  // Initialize animations
  initAnimations();

  // Initialize role filtering if on home page
  if (document.getElementById("category-filter")) {
    initializeRoleFiltering();
  }

  // Form validation & Submission
  const form = document.getElementById("analysis-form");
  if (form) {
    form.addEventListener("submit", function (e) {
      // Basic validation
      const roleSelect = form.querySelector('select[name="role"]');
      const fileInput = form.querySelector('input[name="resume"]');

      let isValid = true;
      let errorMessage = "";

      if (!roleSelect || !roleSelect.value) {
        isValid = false;
        errorMessage = "Please select a target position";
      } else if (!fileInput.files || fileInput.files.length === 0) {
        isValid = false;
        errorMessage = "Please upload your resume";
      } else if (fileInput.files[0]) {
        const file = fileInput.files[0];

        // --- IMAGE SUPPORT ADDED HERE ---
        const validExtensions = [
          ".pdf",
          ".docx",
          ".doc",
          ".jpg",
          ".jpeg",
          ".png",
          ".webp",
        ];
        const fileExtension = file.name
          .substring(file.name.lastIndexOf("."))
          .toLowerCase();

        if (!validExtensions.includes(fileExtension)) {
          isValid = false;
          errorMessage =
            "Please upload PDF, DOCX, or Image (JPG/PNG) files only";
        }

        if (file.size > 10 * 1024 * 1024) {
          isValid = false;
          errorMessage = "File size must be less than 10MB";
        }
      }

      if (!isValid) {
        e.preventDefault();
        showNotification(errorMessage, "error");
        return false;
      }

      // --- Show Loading Overlay ---
      const loadingOverlay = document.getElementById("loading-overlay");
      if (loadingOverlay) {
        // First remove the 'hidden' class (display: none)
        loadingOverlay.classList.remove("hidden");

        // Force a browser reflow so the transition works
        void loadingOverlay.offsetWidth;

        // Then add 'active' (opacity: 1)
        loadingOverlay.classList.add("active");

        // Add AI processing text animation
        const loadingText = loadingOverlay.querySelector(".loading-text");
        if (loadingText) {
          animateAIText(loadingText);
        }

        // Add loading dots animation if missing
        if (!loadingOverlay.querySelector(".loading-dots")) {
          addLoadingDots(loadingOverlay);
        }
      }

      // Update button text
      const analyzeBtn = document.getElementById("analyze-btn");
      if (analyzeBtn) {
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML =
          '<i class="fas fa-hourglass-half fa-spin"></i> Analyzing...';
        analyzeBtn.style.animation = "buttonPress 0.2s ease-out";
      }

      return true;
    });
  }

  // Auto-hide loading if page is loaded/reloaded (prevents stuck spinner)
  const loadingOverlay = document.getElementById("loading-overlay");
  if (loadingOverlay) {
    // If we are just loading the page (not submitting), hide it
    if (!document.querySelector(".loading-overlay.active")) {
      loadingOverlay.classList.add("hidden");
    }
  }
});

/* ============================================
  FILE UPLOAD FUNCTIONS
============================================ */

function initFileUpload() {
  const fileInput = document.querySelector('input[name="resume"]');
  const fileDropArea = document.querySelector(".file-upload");
  const fileMessage = document.querySelector(".file-text");

  if (!fileInput || !fileDropArea) return;

  console.log("📁 File upload initialized");

  // File input change
  fileInput.addEventListener("change", function () {
    console.log("📄 File selected:", this.files[0]?.name);

    if (this.files && this.files.length > 0) {
      const file = this.files[0];
      const fileName = file.name;
      const fileSize = (file.size / (1024 * 1024)).toFixed(2);

      // Update the file message text
      if (fileMessage) {
        fileMessage.innerHTML = `
          <i class="fas fa-file" style="color: var(--primary); margin-bottom: 0.5rem; font-size: 2rem;"></i>
          <div style="font-weight: 600; color: var(--primary); margin-bottom: 0.25rem;">${fileName}</div>
          <div style="font-size: 0.85rem; color: var(--secondary);">${fileSize} MB</div>
        `;
      }

      // Add visual feedback to drop area
      fileDropArea.style.borderColor = "var(--primary)";
      fileDropArea.style.background = "rgba(10, 92, 54, 0.05)";

      // Add success animation
      showSuccessAnimation(fileDropArea, "✓ File uploaded successfully");

      // Remove the upload icon and default text
      const fileIcon = fileDropArea.querySelector(".file-icon");
      const fileHint = fileDropArea.querySelector(".file-hint");
      if (fileIcon) fileIcon.style.display = "none";
      if (fileHint) fileHint.style.display = "none";
    }
  });

  // Drag & drop with animations
  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    fileDropArea.addEventListener(eventName, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  ["dragenter", "dragover"].forEach((eventName) => {
    fileDropArea.addEventListener(eventName, highlight, false);
  });

  ["dragleave", "drop"].forEach((eventName) => {
    fileDropArea.addEventListener(eventName, unhighlight, false);
  });

  function highlight() {
    fileDropArea.style.borderColor = "var(--primary)";
    fileDropArea.style.background = "rgba(10, 92, 54, 0.1)";
    fileDropArea.style.transform = "scale(1.02)";
    fileDropArea.style.boxShadow = "0 8px 25px rgba(10, 92, 54, 0.15)";
  }

  function unhighlight() {
    fileDropArea.style.borderColor = "rgba(212, 175, 55, 0.3)";
    fileDropArea.style.background = "rgba(255, 255, 255, 0.8)";
    fileDropArea.style.transform = "";
    fileDropArea.style.boxShadow = "";
  }

  fileDropArea.addEventListener("drop", handleDrop, false);

  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    if (files.length > 0) {
      fileInput.files = files;
      const event = new Event("change", { bubbles: true });
      fileInput.dispatchEvent(event);
    }
  }
}

function showSuccessAnimation(element, message) {
  // Remove any existing success animation
  const existing = element.querySelector(".success-animation");
  if (existing) existing.remove();

  const success = document.createElement("div");
  success.className = "success-animation";
  success.innerHTML = `
    <i class="fas fa-check-circle"></i>
    <span>${message}</span>
  `;

  success.style.cssText = `
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) scale(0);
    background: var(--success);
    color: white;
    padding: 0.75rem 1.25rem;
    border-radius: var(--radius);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    animation: zoomIn 0.5s ease-out forwards;
    z-index: 10;
    white-space: nowrap;
    box-shadow: var(--shadow-md);
    border: 2px solid white;
    font-size: 0.9rem;
  `;

  element.style.position = "relative"; // Ensure positioning context
  element.appendChild(success);

  setTimeout(() => {
    success.style.animation = "zoomOut 0.5s ease-out forwards";
    setTimeout(() => success.remove(), 500);
  }, 1500);
}

/* ============================================
  ROLE FILTERING FUNCTIONALITY
============================================ */

function initializeRoleFiltering() {
  const categoryFilter = document.getElementById("category-filter");
  const roleSelect = document.getElementById("role-select");

  if (!categoryFilter || !roleSelect) return;

  console.log("🎯 Role filtering initialized");

  // Store all options for filtering (clone them)
  // Skip the first placeholder option
  const allOptions = [];
  roleSelect.querySelectorAll("option").forEach((option) => {
    if (option.value && option.dataset.category) {
      allOptions.push({
        element: option.cloneNode(true),
        category: option.dataset.category,
        value: option.value,
        text: option.textContent,
      });
    }
  });

  // Get placeholder
  const placeholder = roleSelect.querySelector('option[value=""]');

  // --- GLOBAL FUNCTION for HTML onchange ---
  window.filterRoles = function () {
    const selectedCategory = categoryFilter.value;

    // Clear current options
    roleSelect.innerHTML = "";

    // Add placeholder back
    if (placeholder) {
      roleSelect.appendChild(placeholder.cloneNode(true));
    } else {
      roleSelect.innerHTML =
        '<option value="">Select your desired role...</option>';
    }

    // Add filtered options
    allOptions.forEach((option) => {
      if (selectedCategory === "all" || option.category === selectedCategory) {
        roleSelect.appendChild(option.element.cloneNode(true));
      }
    });

    // Show category-specific tip
    showCategoryTip(selectedCategory);

    console.log(
      `🔄 Filtered roles for category: ${selectedCategory}, found ${
        roleSelect.options.length - 1
      } roles`
    );
  };
}

function showCategoryTip(category) {
  const tips = {
    Legal:
      "💼 Tip: Highlight case experience, certifications (Bar), and ethical considerations.",
    Medical:
      "🏥 Tip: Emphasize licenses, specialties, patient care experience, and CME credits.",
    Finance:
      "💰 Tip: Showcase certifications (CA/CPA), analytical skills, and compliance knowledge.",
    Technology:
      "💻 Tip: Highlight technical skills, projects, frameworks, and continuous learning.",
    Engineering:
      "🔧 Tip: Showcase design experience, certifications, and project management.",
    Business:
      "📈 Tip: Focus on leadership, strategy, and measurable business impact.",
    Education:
      "🎓 Tip: Highlight teaching experience, certifications, and curriculum development.",
    Creative:
      "🎨 Tip: Showcase portfolio pieces, creative process, and client projects.",
    Design:
      "🏛️ Tip: Highlight design skills, software proficiency, and project experience.",
    all: "📄 Upload your resume for comprehensive analysis across all industries.",
  };

  const tip = tips[category] || tips["all"];

  // Update file hint text
  const fileHint = document.querySelector(".file-hint");
  if (fileHint) {
    fileHint.innerHTML = `Maximum file size: 10MB<br><span style="color: var(--primary); font-weight: 500; display: block; margin-top: 5px;">💡 ${tip}</span>`;
  }
}

/* ============================================
  ANIMATION FUNCTIONS
============================================ */

function initAnimations() {
  // Initialize scroll animations
  setupScrollAnimations();

  // Initialize hover animations
  setupHoverAnimations();

  // Initialize page-specific animations
  if (document.querySelector(".score-circle")) {
    setupResultPageAnimations();
  }
}

function setupScrollAnimations() {
  // Create intersection observer for scroll animations
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const element = entry.target;

          // Add animation class based on data attribute
          if (element.dataset.animation) {
            element.classList.add(element.dataset.animation);
            element.classList.add("animate-fill-forwards");
          }

          // Also simply unhide anything with animate- classes
          element.style.opacity = "1";
          element.style.animationPlayState = "running";

          observer.unobserve(element);
        }
      });
    },
    {
      threshold: 0.1,
      rootMargin: "0px 0px -50px 0px",
    }
  );

  // Observe all elements with animation attributes
  document
    .querySelectorAll("[data-animation], [class*='animate-']")
    .forEach((el) => {
      observer.observe(el);
    });
}

function setupHoverAnimations() {
  // Card hover animations
  document
    .querySelectorAll(".card, .feature-card, .stat-card")
    .forEach((card) => {
      card.addEventListener("mouseenter", () => {
        card.style.transform = "translateY(-5px)";
        card.style.boxShadow = "0 20px 40px rgba(0, 0, 0, 0.15)";
        card.style.transition = "all 0.3s ease";
      });

      card.addEventListener("mouseleave", () => {
        card.style.transform = "";
        card.style.boxShadow = "";
      });
    });

  // Button hover animations
  document.querySelectorAll(".btn, .primary-button").forEach((btn) => {
    btn.addEventListener("mouseenter", () => {
      btn.style.transform = "translateY(-2px) scale(1.02)";
    });

    btn.addEventListener("mouseleave", () => {
      btn.style.transform = "";
    });

    btn.addEventListener("click", (e) => {
      // Add press animation
      btn.style.animation = "buttonPress 0.2s ease-out";
      setTimeout(() => {
        btn.style.animation = "";
      }, 200);
    });
  });

  // Feature card icon animations
  document.querySelectorAll(".feature-card").forEach((card, index) => {
    card.addEventListener("mouseenter", () => {
      const icon = card.querySelector(".feature-icon");
      if (icon) {
        icon.style.animation = "pulse 0.5s ease-out";
      }
    });
  });
}

function setupResultPageAnimations() {
  // Animate score circle
  const scoreCircle = document.querySelector(".score-circle");
  if (scoreCircle) {
    setTimeout(() => {
      animateScoreCircle(scoreCircle);
    }, 500);
  }

  // Animate skill tags with stagger
  const skillTags = document.querySelectorAll(".skill-tag");
  skillTags.forEach((tag, index) => {
    tag.style.animationDelay = `${index * 0.1}s`;
    tag.classList.add("animate-fade-in");
  });

  // Check if score is high for celebration
  if (scoreCircle) {
    const score = parseInt(scoreCircle.getAttribute("data-score") || "0");
    if (score >= 80) {
      setTimeout(() => {
        launchConfetti();
        showCelebration(score);
      }, 2000);
    }
  }
}

function animateScoreCircle(circle) {
  const score = parseInt(circle.getAttribute("data-score") || "0");
  const valueElement = circle.querySelector(".score-value");

  let currentScore = 0;
  const increment = score / 50;

  const interval = setInterval(() => {
    currentScore += increment;
    if (currentScore >= score) {
      currentScore = score;
      clearInterval(interval);
    }

    if (valueElement) {
      valueElement.textContent = Math.round(currentScore) + "%";
    }

    circle.style.setProperty("--score-percent", currentScore + "%");
  }, 20);
}

function animateAIText(element) {
  const texts = [
    "🤖 AI is analyzing your resume...",
    "📷 Reading image content (OCR)...",
    "🔍 Identifying skill gaps...",
    "📊 Calculating score...",
    "🎯 Generating roadmap...",
    "✨ Preparing report...",
  ];

  let index = 0;

  const interval = setInterval(() => {
    element.textContent = texts[index];
    element.style.opacity = 0;
    setTimeout(() => {
      element.style.opacity = 1;
    }, 300);
    index = (index + 1) % texts.length;
  }, 2000);

  // Store interval ID for cleanup
  element.dataset.intervalId = interval;
}

function addLoadingDots(container) {
  // Check if already exists
  if (container.querySelector(".loading-dots")) return;

  const dots = document.createElement("div");
  dots.className = "loading-dots";
  dots.innerHTML = `
    <span></span>
    <span></span>
    <span></span>
  `;

  container.appendChild(dots);
}

function launchConfetti() {
  const confettiCount = 50;
  const colors = [
    "var(--primary)",
    "var(--secondary)",
    "var(--accent)",
    "var(--success)",
    "var(--warning)",
    "#3B82F6",
    "#10B981",
    "#F59E0B",
    "#8B5CF6",
  ];

  for (let i = 0; i < confettiCount; i++) {
    setTimeout(() => {
      const confetti = document.createElement("div");
      confetti.className = "confetti";

      // Random properties
      const size = Math.random() * 10 + 5;
      const left = Math.random() * 100;
      const delay = Math.random() * 0.5;
      const duration = Math.random() * 3 + 2;
      const color = colors[Math.floor(Math.random() * colors.length)];
      const shape = Math.random() > 0.5 ? "50%" : "2px";

      confetti.style.cssText = `
        position: fixed;
        width: ${size}px;
        height: ${size}px;
        background: ${color};
        top: -20px;
        left: ${left}%;
        border-radius: ${shape};
        opacity: 0;
        animation: confettiRain ${duration}s ease-out ${delay}s forwards;
        z-index: 9999;
        pointer-events: none;
      `;

      document.body.appendChild(confetti);

      // Remove after animation
      setTimeout(() => {
        confetti.remove();
      }, (duration + delay + 1) * 1000);
    }, i * 20);
  }
}

function showCelebration(score) {
  const celebration = document.createElement("div");
  celebration.className = "celebration";
  celebration.innerHTML = `
    <div style="text-align: center;">
      <i class="fas fa-trophy fa-3x" style="color: gold; margin-bottom: 1rem;"></i>
      <h3 style="color: white; margin-bottom: 0.5rem; font-size: 1.5rem;">
        🎉 Excellent Career Match! 🎉
      </h3>
      <p style="color: rgba(255, 255, 255, 0.9);">
        You scored ${score}% - Strong candidate for your chosen career path!
      </p>
    </div>
  `;

  celebration.style.cssText = `
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) scale(0);
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    color: white;
    padding: 2rem;
    border-radius: var(--radius-xl);
    text-align: center;
    z-index: 10000;
    animation: zoomIn 0.5s ease-out 0.5s forwards;
    box-shadow: var(--shadow-xl);
    max-width: 300px;
    border: 3px solid var(--accent);
  `;

  document.body.appendChild(celebration);

  // Remove after 3 seconds
  setTimeout(() => {
    celebration.style.animation = "zoomOut 0.5s ease-out forwards";
    setTimeout(() => celebration.remove(), 500);
  }, 3000);
}

/* ============================================
  NOTIFICATION SYSTEM
============================================ */

function showNotification(message, type = "info") {
  // Create notification element
  const notification = document.createElement("div");
  notification.className = `notification notification-${type}`;

  let icon = "info-circle";
  if (type === "success") icon = "check-circle";
  if (type === "error") icon = "exclamation-circle";

  notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${icon}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close">&times;</button>
    `;

  // Add styles if not present
  if (!document.querySelector("#notification-styles")) {
    const style = document.createElement("style");
    style.id = "notification-styles";
    style.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                background: rgba(30, 41, 59, 0.95);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 1rem 1.5rem;
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1rem;
                min-width: 300px;
                max-width: 400px;
                transform: translateX(150%);
                transition: transform 0.3s ease;
                z-index: 10000;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
                color: white;
            }
            .notification-error {
                border-left: 4px solid #ef4444;
            }
            .notification-success {
                border-left: 4px solid #10b981;
            }
            .notification-info {
                border-left: 4px solid var(--primary);
            }
            .notification.show {
                transform: translateX(0);
            }
            .notification-content {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                flex: 1;
            }
            .notification-close {
                background: none;
                border: none;
                font-size: 1.5rem;
                cursor: pointer;
                color: #94a3b8;
                line-height: 1;
            }
            .notification i {
                font-size: 1.2rem;
            }
            .notification-error i { color: #ef4444; }
            .notification-success i { color: #10b981; }
            .notification-info i { color: var(--primary); }
        `;
    document.head.appendChild(style);
  }

  document.body.appendChild(notification);

  // Show notification with animation
  setTimeout(() => notification.classList.add("show"), 10);

  // Auto remove
  setTimeout(() => {
    notification.classList.remove("show");
    setTimeout(() => notification.remove(), 300);
  }, 5000);

  // Close button
  notification
    .querySelector(".notification-close")
    .addEventListener("click", () => {
      notification.classList.remove("show");
      setTimeout(() => notification.remove(), 300);
    });
}

/* ============================================
  DOWNLOAD REPORT FUNCTION
============================================ */

function downloadReport() {
  const btn = document.getElementById("download-btn");
  if (!btn) return;

  const originalText = btn.innerHTML;
  const roleSpan = document.querySelector(".highlight-text");
  const role = roleSpan ? roleSpan.textContent : "Career";

  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating Report...';

  fetch("/download-report")
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.blob();
    })
    .then((blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `SkillBridge_Career_Report_${role.replace(
        /[^a-z0-9]/gi,
        "_"
      )}_${new Date().toISOString().slice(0, 10)}.txt`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      btn.innerHTML = '<i class="fas fa-check"></i> Report Downloaded';
      setTimeout(() => {
        btn.disabled = false;
        btn.innerHTML = originalText;
      }, 2000);

      showNotification("Career report downloaded successfully!", "success");
    })
    .catch((error) => {
      console.error("Download error:", error);
      btn.innerHTML = '<i class="fas fa-times"></i> Failed';
      setTimeout(() => {
        btn.disabled = false;
        btn.innerHTML = originalText;
      }, 2000);

      showNotification("Failed to download report. Please try again.", "error");
    });
}

// --- GLOBAL EXPORTS ---
window.SkillBridge = {
  showNotification,
  downloadReport,
  initFileUpload,
  initializeRoleFiltering,
};
window.downloadReport = downloadReport;
window.showNotification = showNotification;

// Add CSS animation keyframes dynamically
const animationStyles = document.createElement("style");
animationStyles.textContent = `
  @keyframes zoomIn {
    0% {
      opacity: 0;
      transform: scale(0.3);
    }
    100% {
      opacity: 1;
      transform: scale(1);
    }
  }
  
  @keyframes zoomOut {
    0% {
      opacity: 1;
      transform: scale(1);
    }
    100% {
      opacity: 0;
      transform: scale(0.3);
    }
  }
  
  @keyframes buttonPress {
    0% {
      transform: scale(1);
    }
    50% {
      transform: scale(0.95);
    }
    100% {
      transform: scale(1);
    }
  }
  
  @keyframes confettiRain {
    0% {
      transform: translateY(-100px) rotate(0deg);
      opacity: 1;
    }
    100% {
      transform: translateY(100vh) rotate(720deg);
      opacity: 0;
    }
  }
  
  @keyframes wave {
    0%, 60%, 100% {
      transform: translateY(0);
    }
    30% {
      transform: translateY(-10px);
    }
  }
  
  .loading-dots {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin-top: 20px;
  }
  
  .loading-dots span {
    width: 12px;
    height: 12px;
    background: var(--primary);
    border-radius: 50%;
    animation: wave 1s ease-in-out infinite;
  }
  
  .loading-dots span:nth-child(2) {
    animation-delay: 0.2s;
  }
  
  .loading-dots span:nth-child(3) {
    animation-delay: 0.4s;
  }
  
  @keyframes pulse {
    0% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.05);
    }
    100% {
      transform: scale(1);
    }
  }
`;
document.head.appendChild(animationStyles);

// Initialize any page-specific functionality
if (document.getElementById("role-select")) {
  console.log("🎯 Role selection initialized");
}

// Add event listener for download button on result page
document.addEventListener("click", function (e) {
  if (
    e.target &&
    (e.target.id === "download-btn" || e.target.closest("#download-btn"))
  ) {
    downloadReport();
  }
});
