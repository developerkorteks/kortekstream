/**
 * Hero Carousel component functionality for KortekStream
 * Handles automatic slideshow, manual navigation, and pause on hover
 */

// Default configuration
const DEFAULT_CONFIG = {
    autoplay: true,
    interval: 5000,
    pauseOnHover: true
};

/**
 * Hero Carousel class
 */
class HeroCarousel {
    /**
     * Create a new carousel instance
     * @param {string} selector - CSS selector for the carousel container
     * @param {Object} options - Configuration options
     */
    constructor(selector, options = {}) {
        // Merge default config with options
        this.config = { ...DEFAULT_CONFIG, ...options };
        
        // DOM elements
        this.container = document.querySelector(selector);
        if (!this.container) return;
        
        this.slides = this.container.querySelectorAll('.hero-slide');
        this.dots = this.container.querySelectorAll('.hero-dot');
        this.prevBtn = this.container.querySelector('#hero-prev');
        this.nextBtn = this.container.querySelector('#hero-next');
        
        // State
        this.currentSlide = 0;
        this.slideInterval = null;
        
        // Initialize
        this.init();
    }
    
    /**
     * Initialize carousel
     */
    init() {
        if (this.slides.length === 0) return;
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Start autoplay if enabled
        if (this.config.autoplay) {
            this.startAutoplay();
        }
    }
    
    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Dot navigation
        this.dots.forEach((dot, index) => {
            dot.addEventListener('click', () => {
                this.goToSlide(index);
            });
        });
        
        // Previous/Next buttons
        if (this.prevBtn) {
            this.prevBtn.addEventListener('click', () => {
                this.prevSlide();
            });
        }
        
        if (this.nextBtn) {
            this.nextBtn.addEventListener('click', () => {
                this.nextSlide();
            });
        }
        
        // Pause on hover
        if (this.config.pauseOnHover) {
            this.container.addEventListener('mouseenter', () => {
                this.pauseAutoplay();
            });
            
            this.container.addEventListener('mouseleave', () => {
                if (this.config.autoplay) {
                    this.startAutoplay();
                }
            });
        }
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') {
                this.prevSlide();
            } else if (e.key === 'ArrowRight') {
                this.nextSlide();
            }
        });
    }
    
    /**
     * Go to a specific slide
     * @param {number} index - Slide index
     */
    goToSlide(index) {
        // Validate index
        if (index < 0 || index >= this.slides.length) return;
        
        // Hide all slides
        this.slides.forEach(slide => {
            slide.classList.remove('opacity-100');
            slide.classList.add('opacity-0');
        });
        
        // Update dots
        this.dots.forEach(dot => {
            dot.classList.remove('bg-white');
            dot.classList.add('bg-white/50');
        });
        
        // Show the selected slide
        this.slides[index].classList.remove('opacity-0');
        this.slides[index].classList.add('opacity-100');
        
        // Update the selected dot
        if (this.dots[index]) {
            this.dots[index].classList.remove('bg-white/50');
            this.dots[index].classList.add('bg-white');
        }
        
        // Update current slide index
        this.currentSlide = index;
        
        // Reset autoplay timer
        if (this.config.autoplay) {
            this.pauseAutoplay();
            this.startAutoplay();
        }
    }
    
    /**
     * Go to the next slide
     */
    nextSlide() {
        let next = this.currentSlide + 1;
        if (next >= this.slides.length) {
            next = 0;
        }
        this.goToSlide(next);
    }
    
    /**
     * Go to the previous slide
     */
    prevSlide() {
        let prev = this.currentSlide - 1;
        if (prev < 0) {
            prev = this.slides.length - 1;
        }
        this.goToSlide(prev);
    }
    
    /**
     * Start autoplay
     */
    startAutoplay() {
        this.slideInterval = setInterval(() => {
            this.nextSlide();
        }, this.config.interval);
    }
    
    /**
     * Pause autoplay
     */
    pauseAutoplay() {
        clearInterval(this.slideInterval);
    }
}

/**
 * Initialize hero carousel on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    const heroCarousel = new HeroCarousel('#hero-carousel');
});

// Export for potential use in other modules
export default HeroCarousel;