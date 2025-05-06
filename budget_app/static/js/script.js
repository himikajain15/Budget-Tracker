// script.js

// Toggle dark mode
function toggleDarkMode() {
    const body = document.body;
    const currentMode = body.classList.contains('dark-mode');
    
    if (currentMode) {
        body.classList.remove('dark-mode');
        localStorage.setItem('theme', 'light');
    } else {
        body.classList.add('dark-mode');
        localStorage.setItem('theme', 'dark');
    }
}

// Load theme from localStorage
document.addEventListener('DOMContentLoaded', () => {
    const theme = localStorage.getItem('theme');
    if (theme === 'dark') {
        document.body.classList.add('dark-mode');
    }
});
