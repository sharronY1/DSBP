const API_BASE = "";
const licenseForm = document.getElementById("license-form");
const licenseFileForm = document.getElementById("license-file-form");
const errorEl = document.getElementById("license-error");
const token = localStorage.getItem("kanban_token");

if (!token) {
  window.location.href = "/login";
}

function showError(message) {
  if (!errorEl) return;
  errorEl.textContent = message;
  errorEl.classList.remove("hidden");
}

function clearError() {
  if (!errorEl) return;
  errorEl.classList.add("hidden");
}

async function handleLicenseActivate(event) {
  event.preventDefault();
  clearError();
  
  const formData = new FormData(licenseForm);
  const licenseKey = formData.get("license_key")?.trim().toUpperCase();
  
  if (!licenseKey) {
    showError("Please enter a license key.");
    return;
  }
  
  const submitButton = licenseForm.querySelector("button[type='submit']");
  if (submitButton) {
    submitButton.disabled = true;
    submitButton.textContent = "Activating...";
  }
  
  try {
    const response = await fetch(`${API_BASE}/licenses/activate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ license_key: licenseKey })
    });
    
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || "Failed to activate license");
    }
    
    alert("License activated successfully!");
    window.location.href = "/";
  } catch (error) {
    showError(error.message);
  } finally {
    if (submitButton) {
      submitButton.disabled = false;
      submitButton.textContent = "Activate License";
    }
  }
}

async function handleLicenseFileUpload(event) {
  event.preventDefault();
  clearError();
  
  const fileInput = document.getElementById("license-file");
  const file = fileInput.files[0];
  
  if (!file) {
    showError("Please select a license file.");
    return;
  }
  
  const submitButton = licenseFileForm.querySelector("button[type='submit']");
  if (submitButton) {
    submitButton.disabled = true;
    submitButton.textContent = "Uploading...";
  }
  
  try {
    const formData = new FormData();
    formData.append("file", file);
    
    const response = await fetch(`${API_BASE}/licenses/upload`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`
      },
      body: formData
    });
    
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || "Failed to upload license file");
    }
    
    alert("License activated successfully!");
    window.location.href = "/";
  } catch (error) {
    showError(error.message);
  } finally {
    if (submitButton) {
      submitButton.disabled = false;
      submitButton.textContent = "Upload and Activate";
    }
  }
}

if (licenseForm) {
  licenseForm.addEventListener("submit", handleLicenseActivate);
}

if (licenseFileForm) {
  licenseFileForm.addEventListener("submit", handleLicenseFileUpload);
}

