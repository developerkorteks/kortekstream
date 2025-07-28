/**
 * Tabs component functionality for KortekStream
 * Handles tab switching and URL parameter synchronization
 */

/**
 * Tabs class
 */
class Tabs {
    /**
     * Create a new tabs instance
     * @param {string} selector - CSS selector for the tabs container
     * @param {Object} options - Configuration options
     */
    constructor(selector, options = {}) {
        // Default options
        this.options = {
            defaultTab: 'watchlist',
            useUrlParams: true,
            paramName: 'tab',
            ...options
        };
        
        // DOM elements
        this.container = document.querySelector(selector);
        if (!this.container) return;
        
        this.tabButtons = this.container.querySelectorAll('[data-tabs-target]');
        this.tabContents = document.querySelectorAll('[role="tabpanel"]');
        
        // Initialize
        this.init();
    }
    
    /**
     * Initialize tabs
     */
    init() {
        if (this.tabButtons.length === 0) return;
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Activate tab from URL parameter or default
        this.activateTabFromUrlOrDefault();
    }
    
    /**
     * Set up event listeners
     */
    setupEventListeners() {
        this.tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetId = button.getAttribute('data-tabs-target').substring(1);
                this.activateTab(targetId);
                
                // Update URL parameter if enabled
                if (this.options.useUrlParams) {
                    this.updateUrlParameter(targetId);
                }
            });
        });
    }
    
    /**
     * Activate tab from URL parameter or default
     */
    activateTabFromUrlOrDefault() {
        let activeTab = this.options.defaultTab;
        
        // Check for tab in URL parameter
        if (this.options.useUrlParams) {
            const urlParams = new URLSearchParams(window.location.search);
            const tabParam = urlParams.get(this.options.paramName);
            
            if (tabParam) {
                activeTab = tabParam;
            }
        }
        
        // Find the tab button and activate it
        const tabButton = document.getElementById(`${activeTab}-tab`);
        if (tabButton) {
            tabButton.click();
        } else {
            // If specified tab doesn't exist, activate the first tab
            if (this.tabButtons[0]) {
                this.tabButtons[0].click();
            }
        }
    }
    
    /**
     * Activate a specific tab
     * @param {string} tabId - ID of the tab to activate
     */
    activateTab(tabId) {
        // Hide all tab contents
        this.tabContents.forEach(content => {
            content.classList.add('hidden');
            content.classList.remove('block');
        });
        
        // Remove active state from all buttons
        this.tabButtons.forEach(btn => {
            btn.classList.remove('border-primary', 'dark:border-darkPrimary', 'text-primary', 'dark:text-darkPrimary');
            btn.classList.add('border-transparent');
            btn.setAttribute('aria-selected', 'false');
        });
        
        // Show the selected tab content
        const targetContent = document.getElementById(tabId);
        if (targetContent) {
            targetContent.classList.remove('hidden');
            targetContent.classList.add('block');
        }
        
        // Set active state to clicked button
        const activeButton = document.querySelector(`[data-tabs-target="#${tabId}"]`);
        if (activeButton) {
            activeButton.classList.remove('border-transparent');
            activeButton.classList.add('border-primary', 'dark:border-darkPrimary', 'text-primary', 'dark:text-darkPrimary');
            activeButton.setAttribute('aria-selected', 'true');
        }
    }
    
    /**
     * Update URL parameter
     * @param {string} tabId - ID of the active tab
     */
    updateUrlParameter(tabId) {
        const url = new URL(window.location);
        url.searchParams.set(this.options.paramName, tabId);
        window.history.replaceState({}, '', url);
    }
}

/**
 * Initialize tabs on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize collection tabs if present
    const collectionTabs = new Tabs('#collection-tabs', {
        defaultTab: 'watchlist',
        useUrlParams: true,
        paramName: 'tab'
    });
});

// Export for potential use in other modules
export default Tabs;