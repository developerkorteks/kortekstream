/**
 * Navbar component functionality for KortekStream
 * Handles mobile menu toggle
 */

// DOM Elements
const mobileMenuButton = document.getElementById('mobile-menu-button');
const mobileMenu = document.getElementById('mobile-menu');

/**
 * Toggle mobile menu visibility
 */
function toggleMobileMenu() {
    if (mobileMenu) {
        mobileMenu.classList.toggle('hidden');
    }
}

/**
 * Close mobile menu when clicking outside
 * @param {Event} event - The click event
 */
function handleOutsideClick(event) {
    // If mobile menu is open and click is outside the menu and the toggle button
    if (
        mobileMenu && 
        !mobileMenu.classList.contains('hidden') && 
        !mobileMenu.contains(event.target) && 
        !mobileMenuButton.contains(event.target)
    ) {
        mobileMenu.classList.add('hidden');
    }
}

/**
 * Initialize navbar functionality
 */
function initNavbar() {
    // Add event listener to mobile menu button
    if (mobileMenuButton) {
        mobileMenuButton.addEventListener('click', toggleMobileMenu);
    }
    
    // Add event listener to close mobile menu when clicking outside
    document.addEventListener('click', handleOutsideClick);
    
    // Close mobile menu on window resize (e.g., when switching to desktop view)
    window.addEventListener('resize', () => {
        if (mobileMenu && window.innerWidth >= 768) { // 768px is the md breakpoint in Tailwind
            mobileMenu.classList.add('hidden');
        }
    });
}

// Initialize navbar on page load
document.addEventListener('DOMContentLoaded', initNavbar);

// Export functions for potential use in other modules
export { toggleMobileMenu, initNavbar };