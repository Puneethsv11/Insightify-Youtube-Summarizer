document.addEventListener('DOMContentLoaded', function() {
    const videoURLParam = new URLSearchParams(window.location.search).get('video_url');
    if (videoURLParam) {
        document.getElementById('videoURL').value = videoURLParam;
    }
});

// Event listener for the save button
document.getElementById('saveButton').addEventListener('click', function() {
    const summary = document.getElementById('summary').textContent.trim();
    const video_url = new URL(window.location.href).searchParams.get('video_url');
    const type = document.getElementById('summaryType').value;

    fetch('/save_summary', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ summary: summary, video_url: video_url, type: type })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.message) {
            alert(data.message);
        } else {
            alert('Unknown response from server');
        }
    })
    .catch(error => {
        alert('Error saving summary and video link: ' + error.message);
        console.error('Error saving summary and video link:', error);
    });
});

// Function to open sidebar
function openSidebar() {
    document.getElementById("mySidebar").style.left = "0";
}

// Function to close sidebar
function closeSidebar() {
    document.getElementById("mySidebar").style.left = "-250px";
}

// Function to toggle dropdown content
function toggleDropdown(id) {
    var content = document.getElementById(id);
    if (content.style.display === "block") {
        content.style.display = "none";
    } else {
        content.style.display = "block";
    }
}

// Event listeners for dropdowns
document.querySelectorAll('.type').forEach(typeElement => {
    typeElement.addEventListener('click', function() {
        const id = this.getAttribute('data-dropdown');
        toggleDropdown(id);
    });
});
