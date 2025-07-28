/**
 * Theme management for KortekStream
 * Handles switching between light and dark mode
 */

// DOM Elements
const themeToggleButton = document.getElementById('theme-toggle');
const htmlElement = document.documentElement;

/**
 * Initialize theme based on localStorage or default to dark
 */
function initTheme() {
    // Set dark mode as default if no preference is saved
    if (!localStorage.getItem('theme')) {
        localStorage.setItem('theme', 'dark');
    }
    
    // Apply saved theme preference
    if (localStorage.getItem('theme') === 'light') {
        htmlElement.classList.remove('dark');
    } else {
        htmlElement.classList.add('dark');
    }
    
    // Update theme toggle button icons
    updateThemeToggleIcons();
}

/**
 * Toggle between light and dark theme
 */
function toggleTheme() {
    // Toggle dark class on html element
    htmlElement.classList.toggle('dark');
    
    // Save theme preference to localStorage
    if (htmlElement.classList.contains('dark')) {
        localStorage.setItem('theme', 'dark');
    } else {
        localStorage.setItem('theme', 'light');
    }
    
    // Update theme toggle button icons
    updateThemeToggleIcons();
}

/**
 * Update theme toggle button icons based on current theme
 */
function updateThemeToggleIcons() {
    const sunIcon = themeToggleButton.querySelector('.fa-sun');
    const moonIcon = themeToggleButton.querySelector('.fa-moon');
    
    if (htmlElement.classList.contains('dark')) {
        sunIcon.classList.add('hidden');
        moonIcon.classList.remove('hidden');
    } else {
        sunIcon.classList.remove('hidden');
        moonIcon.classList.add('hidden');
    }
}

// Event Listeners
if (themeToggleButton) {
    themeToggleButton.addEventListener('click', toggleTheme);
}

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', initTheme);

// Export functions for potential use in other modules
export { initTheme, toggleTheme };