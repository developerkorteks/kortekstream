/**
 * Dynamic Border component for KortekStream
 * Extracts dominant color from anime cover images and applies it to card borders on hover
 */

/**
 * Set dynamic border color based on image
 * @param {HTMLElement} cardElement - The card element
 * @param {HTMLImageElement} imageElement - The image element
 */
function setDynamicBorderColor(cardElement, imageElement) {
    if (!cardElement || !imageElement) return;
    
    // Create canvas to analyze image
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    
    // When image is loaded
    imageElement.addEventListener('load', function() {
        // Skip if image is not loaded properly
        if (!this.complete || this.naturalWidth === 0) return;
        
        try {
            // Set canvas dimensions to match image
            canvas.width = this.width;
            canvas.height = this.height;
            
            // Draw image on canvas
            context.drawImage(this, 0, 0, this.width, this.height);
            
            // Get pixel data from the center of the image
            const imageData = context.getImageData(
                Math.floor(this.width / 2), 
                Math.floor(this.height / 2), 
                1, 1
            ).data;
            
            // Convert RGB to hex
            const color = `#${imageData[0].toString(16).padStart(2, '0')}${imageData[1].toString(16).padStart(2, '0')}${imageData[2].toString(16).padStart(2, '0')}`;
            
            // Apply color to card border on hover
            cardElement.addEventListener('mouseenter', function() {
                this.style.borderColor = color;
                
                // Also apply color to title if it exists
                const titleElement = this.querySelector('.title');
                if (titleElement) {
                    titleElement.style.color = color;
                }
            });
            
            // Reset on mouse leave
            cardElement.addEventListener('mouseleave', function() {
                this.style.borderColor = '';
                
                // Reset title color
                const titleElement = this.querySelector('.title');
                if (titleElement) {
                    titleElement.style.color = '';
                }
            });
        } catch (error) {
            console.error('Error setting dynamic border color:', error);
        }
    });
    
    // Handle image load errors
    imageElement.addEventListener('error', function() {
        console.warn('Failed to load image for dynamic border color');
    });
}

/**
 * Initialize dynamic borders for all anime cards
 */
function initDynamicBorders() {
    const animeCards = document.querySelectorAll('.anime-card');
    
    animeCards.forEach(card => {
        const image = card.querySelector('img');
        if (image) {
            setDynamicBorderColor(card, image);
        }
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initDynamicBorders);

// Export for potential use in other modules
export { setDynamicBorderColor, initDynamicBorders };