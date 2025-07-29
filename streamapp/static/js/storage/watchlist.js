/**
 * Watchlist functionality for KortekStream
 * Handles storing and retrieving anime watchlist data in localStorage
 */

// Constants
const STORAGE_KEY = 'kortekstream_watchlist';

/**
 * Get watchlist from localStorage
 * @returns {Array} Array of watchlist items
 */
function getWatchlist() {
    try {
        const watchlist = localStorage.getItem(STORAGE_KEY);
        return watchlist ? JSON.parse(watchlist) : [];
    } catch (error) {
        console.error('Error getting watchlist:', error);
        return [];
    }
}

/**
 * Add anime to watchlist
 * @param {number|null} animeId - Anime ID (optional)
 * @param {string} title - Anime title
 * @param {string} slug - Anime slug
 * @param {string} cover - Anime cover image URL
 * @returns {boolean} Success status
 */
function addToWatchlist(animeId, title, slug, cover) {
    try {
        const watchlist = getWatchlist();
        
        // Check if anime is already in watchlist
        if (!watchlist.some(item => item.slug === slug)) {
            watchlist.push({
                id: animeId || Date.now(),
                title: title,
                slug: slug,
                cover: cover,
                addedAt: new Date().toISOString()
            });
            
            localStorage.setItem(STORAGE_KEY, JSON.stringify(watchlist));
            return true;
        }
        return false;
    } catch (error) {
        console.error('Error adding to watchlist:', error);
        return false;
    }
}

/**
 * Remove anime from watchlist
 * @param {string} slug - Anime slug
 * @returns {boolean} Success status
 */
function removeFromWatchlist(slug) {
    try {
        let watchlist = getWatchlist();
        watchlist = watchlist.filter(item => item.slug !== slug);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(watchlist));
        return true;
    } catch (error) {
        console.error('Error removing from watchlist:', error);
        return false;
    }
}

/**
 * Check if anime is in watchlist
 * @param {string} slug - Anime slug
 * @returns {boolean} True if anime is in watchlist
 */
function isInWatchlist(slug) {
    const watchlist = getWatchlist();
    return watchlist.some(item => item.slug === slug);
}

/**
 * Clear entire watchlist
 * @returns {boolean} Success status
 */
function clearWatchlist() {
    try {
        localStorage.removeItem(STORAGE_KEY);
        return true;
    } catch (error) {
        console.error('Error clearing watchlist:', error);
        return false;
    }
}

/**
 * Update watchlist UI elements
 * @param {string} slug - Anime slug
 * @param {boolean|null} isAdded - Whether anime is added (null to check)
 */
function updateWatchlistUI(slug, isAdded = null) {
    // Find watchlist button
    const btn = document.getElementById('watchlist-btn');
    const icon = document.getElementById('watchlist-icon');
    const text = document.getElementById('watchlist-text');
    
    if (!btn || !icon || !text) return;
    
    const inWatchlist = isAdded !== null ? isAdded : isInWatchlist(slug);
    
    if (inWatchlist) {
        btn.classList.remove('bg-primary/80');
        btn.classList.add('bg-green-500/80');
        icon.classList.remove('fa-bookmark');
        icon.classList.add('fa-check');
        text.textContent = 'Dalam Watchlist';
    } else {
        btn.classList.remove('bg-green-500/80');
        btn.classList.add('bg-primary/80');
        icon.classList.remove('fa-check');
        icon.classList.add('fa-bookmark');
        text.textContent = 'Tambah ke Watchlist';
    }
}

/**
 * Toggle anime in watchlist
 * @param {string} title - Anime title
 * @param {string} slug - Anime slug
 * @param {string} cover - Anime cover image URL
 * @returns {boolean} New watchlist status
 */
function toggleWatchlist(title, slug, cover) {
    const inWatchlist = isInWatchlist(slug);
    
    if (inWatchlist) {
        removeFromWatchlist(slug);
        updateWatchlistUI(slug, false);
        showNotification('Dihapus dari watchlist');
        return false;
    } else {
        addToWatchlist(null, title, slug, cover);
        updateWatchlistUI(slug, true);
        showNotification('Ditambahkan ke watchlist');
        return true;
    }
}

/**
 * Load watchlist into container
 * @param {string} containerId - ID of container element
 */
function loadWatchlist(containerId = 'watchlist-container') {
    // Log untuk verifikasi perubahan
    console.log("Memuat watchlist dengan link ke detail anime");
    
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const watchlist = getWatchlist();
    
    // Log untuk memverifikasi data watchlist
    if (watchlist.length > 0) {
        console.log("Contoh item watchlist pertama:", {
            title: watchlist[0].title,
            slug: watchlist[0].slug,
            linkDetailAnime: `/anime/${watchlist[0].slug}`
        });
    }
    
    if (watchlist.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12 col-span-full">
                <i class="fas fa-bookmark text-gray-300 dark:text-gray-600 text-5xl mb-4"></i>
                <p class="text-gray-500 dark:text-gray-400">Watchlist Anda kosong</p>
                <p class="text-gray-500 dark:text-gray-400 text-sm mt-2">Tambahkan anime ke watchlist dengan mengklik tombol "Tambah ke Watchlist" di halaman detail anime</p>
            </div>
        `;
        return;
    }
    
    // Sort by added date (newest first)
    watchlist.sort((a, b) => new Date(b.addedAt) - new Date(a.addedAt));
    
    let html = '';
    watchlist.forEach(item => {
        html += `
            <div class="anime-card dynamic-border bg-white dark:bg-darkSecondary rounded-lg overflow-hidden shadow-md hover:shadow-lg transition-all duration-300 border border-gray-200 dark:border-gray-700">
                <a href="${item.slug.includes('/anime/') ? item.slug : `/anime/${item.slug}`}" class="block"
                   onclick="console.log('Navigasi ke: ' + (this.href || window.location.origin + (item.slug.includes('/anime/') ? item.slug : '/anime/' + item.slug)))">
                    <div class="relative pb-[140%] overflow-hidden">
                        <img src="${item.cover}" alt="${item.title}" class="absolute inset-0 w-full h-full object-cover transition-transform duration-300 hover:scale-105">
                        
                        <div class="absolute top-2 right-2 bg-primary dark:bg-darkPrimary text-white text-xs font-bold px-2 py-1 rounded-md">
                            Watchlist
                        </div>
                        
                        <button onclick="event.preventDefault(); removeFromWatchlistAndUpdate('${item.slug}')" class="absolute bottom-2 right-2 bg-red-500 text-white w-8 h-8 rounded-full flex items-center justify-center hover:bg-red-600 transition-colors dark:bg-red-600 dark:hover:bg-red-700">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                    
                    <div class="p-4">
                        <h3 class="title text-sm font-semibold text-gray-800 dark:text-white mb-2 line-clamp-2 h-10">${item.title}</h3>
                        <div class="text-xs text-gray-500 dark:text-gray-400">
                            Ditambahkan: ${formatDate(item.addedAt)}
                        </div>
                    </div>
                </a>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

/**
 * Remove from watchlist and update UI
 * @param {string} slug - Anime slug
 */
function removeFromWatchlistAndUpdate(slug) {
    removeFromWatchlist(slug);
    loadWatchlist();
    showNotification('Dihapus dari watchlist');
}

/**
 * Format date for display
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Show notification
 * @param {string} message - Notification message
 */
function showNotification(message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'fixed bottom-4 right-4 bg-gray-800 text-white px-4 py-2 rounded-lg shadow-lg z-50 animate-fade-in-up dark:bg-black/70 dark:border dark:border-gray-700/50';
    notification.textContent = message;
    
    // Add to DOM
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.classList.add('animate-fade-out');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 500);
    }, 3000);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on the detail page
    const animeSlug = window.location.pathname.split('/').pop();
    const watchlistBtn = document.getElementById('watchlist-btn');
    
    if (watchlistBtn && animeSlug) {
        updateWatchlistUI(animeSlug);
    }
    
    // Check if we're on the collection page
    const watchlistContainer = document.getElementById('watchlist-container');
    if (watchlistContainer) {
        loadWatchlist();
    }
});

// Export for potential use in other modules
export {
    getWatchlist,
    addToWatchlist,
    removeFromWatchlist,
    isInWatchlist,
    clearWatchlist,
    toggleWatchlist,
    loadWatchlist,
    updateWatchlistUI
};