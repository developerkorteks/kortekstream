/**
 * Watch History functionality for KortekStream
 * Handles storing and retrieving anime watch history data in localStorage
 */

// Constants
const STORAGE_KEY = 'kortekstream_history';
const MAX_HISTORY_ITEMS = 100;

/**
 * Get watch history from localStorage
 * @returns {Array} Array of history items
 */
function getWatchHistory() {
    try {
        const history = localStorage.getItem(STORAGE_KEY);
        return history ? JSON.parse(history) : [];
    } catch (error) {
        console.error('Error getting watch history:', error);
        return [];
    }
}

/**
 * Add anime to watch history
 * @param {number|null} animeId - Anime ID (optional)
 * @param {string} title - Anime title
 * @param {string} slug - Anime slug
 * @param {string} episodeSlug - Episode slug
 * @param {string} episodeTitle - Episode title
 * @param {string} cover - Anime cover image URL
 * @returns {boolean} Success status
 */
function addToWatchHistory(animeId, title, slug, episodeSlug, episodeTitle, cover) {
    try {
        let history = getWatchHistory();
        
        // Limit history to MAX_HISTORY_ITEMS items
        if (history.length >= MAX_HISTORY_ITEMS) {
            history = history.slice(0, MAX_HISTORY_ITEMS - 1);
        }
        
        // Remove existing entry with same episode if exists
        history = history.filter(item => item.episodeSlug !== episodeSlug);
        
        // Add to beginning of array (most recent first)
        history.unshift({
            id: animeId || Date.now(),
            title: title,
            slug: slug,
            episodeSlug: episodeSlug,
            episodeTitle: episodeTitle,
            cover: cover,
            watchedAt: new Date().toISOString()
        });
        
        localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
        return true;
    } catch (error) {
        console.error('Error adding to watch history:', error);
        return false;
    }
}

/**
 * Remove episode from watch history
 * @param {string} episodeSlug - Episode slug
 * @returns {boolean} Success status
 */
function removeFromHistory(episodeSlug) {
    try {
        let history = getWatchHistory();
        history = history.filter(item => item.episodeSlug !== episodeSlug);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
        return true;
    } catch (error) {
        console.error('Error removing from history:', error);
        return false;
    }
}

/**
 * Clear entire watch history
 * @returns {boolean} Success status
 */
function clearWatchHistory() {
    try {
        localStorage.removeItem(STORAGE_KEY);
        return true;
    } catch (error) {
        console.error('Error clearing watch history:', error);
        return false;
    }
}

/**
 * Check if episode is in watch history
 * @param {string} episodeSlug - Episode slug
 * @returns {boolean} True if episode is in watch history
 */
function isInWatchHistory(episodeSlug) {
    const history = getWatchHistory();
    return history.some(item => item.episodeSlug === episodeSlug);
}

/**
 * Get most recent watched episodes for an anime
 * @param {string} animeSlug - Anime slug
 * @returns {Array} Array of watched episodes
 */
function getAnimeWatchHistory(animeSlug) {
    const history = getWatchHistory();
    return history.filter(item => item.slug === animeSlug);
}

/**
 * Load watch history into container
 * @param {string} containerId - ID of container element
 */
function loadWatchHistory(containerId = 'history-container') {
    // Log untuk verifikasi perubahan
    console.log("Memuat riwayat tontonan dengan link ke detail anime");
    
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const history = getWatchHistory();
    
    // Log untuk memverifikasi data riwayat
    if (history.length > 0) {
        console.log("Contoh item riwayat pertama:", {
            title: history[0].title,
            slug: history[0].slug,
            rawSlug: history[0].slug,
            linkDetailAnime: `/anime/${history[0].slug}`
        });
        
        // Periksa apakah slug mengandung '/anime/'
        if (history[0].slug.includes('/anime/')) {
            console.error("⚠️ Slug mengandung '/anime/' di dalamnya, ini akan menyebabkan double path di URL");
        }
    }
    
    if (history.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12 col-span-full">
                <i class="fas fa-history text-gray-300 dark:text-gray-600 text-5xl mb-4"></i>
                <p class="text-gray-500 dark:text-gray-400">Riwayat tontonan Anda kosong</p>
                <p class="text-gray-500 dark:text-gray-400 text-sm mt-2">Riwayat akan otomatis ditambahkan saat Anda menonton episode</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    history.forEach(item => {
        html += `
            <div class="anime-card dynamic-border bg-white dark:bg-darkSecondary rounded-lg overflow-hidden shadow-md hover:shadow-lg transition-all duration-300 border border-gray-200 dark:border-gray-700">
                <a href="${item.slug.includes('/anime/') ? item.slug : `/anime/${item.slug}`}" class="block"
                   onclick="console.log('Navigasi ke: ' + (this.href || window.location.origin + (item.slug.includes('/anime/') ? item.slug : '/anime/' + item.slug)))">
                    <div class="relative pb-[140%] overflow-hidden">
                        <img src="${item.cover}" alt="${item.title}" class="absolute inset-0 w-full h-full object-cover transition-transform duration-300 hover:scale-105">
                        
                        <div class="absolute top-2 right-2 bg-gray-800 text-white text-xs font-bold px-2 py-1 rounded-md">
                            <i class="fas fa-play mr-1"></i> Ditonton
                        </div>
                        
                        <button onclick="event.preventDefault(); removeFromHistoryAndUpdate('${item.episodeSlug}')" class="absolute bottom-2 right-2 bg-red-500 text-white w-8 h-8 rounded-full flex items-center justify-center hover:bg-red-600 transition-colors dark:bg-red-600 dark:hover:bg-red-700">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                    
                    <div class="p-4">
                        <h3 class="title text-sm font-semibold text-gray-800 dark:text-white mb-2 line-clamp-2 h-10">${item.episodeTitle}</h3>
                        <div class="flex justify-between items-center text-xs text-gray-500 dark:text-gray-400">
                            <span>${formatDate(item.watchedAt)}</span>
                            <a href="/detail_anime/${item.slug}" class="text-primary dark:text-darkPrimary hover:underline">
                                <i class="fas fa-info-circle mr-1"></i>Detail
                            </a>
                        </div>
                    </div>
                </a>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

/**
 * Remove from history and update UI
 * @param {string} episodeSlug - Episode slug
 */
function removeFromHistoryAndUpdate(episodeSlug) {
    removeFromHistory(episodeSlug);
    loadWatchHistory();
    showNotification('Dihapus dari riwayat');
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

/**
 * Track episode clicks to add to watch history
 */
function trackEpisodeClicks() {
    const episodeLinks = document.querySelectorAll('a[href*="detail_episode_video"]');
    
    episodeLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Get anime info from closest parent
            const card = this.closest('.anime-card');
            if (card) {
                const titleEl = card.querySelector('.title');
                const coverEl = card.querySelector('img');
                
                if (titleEl && coverEl) {
                    const title = titleEl.textContent.trim();
                    const cover = coverEl.src;
                    const href = this.getAttribute('href');
                    const episodeSlug = href.split('/').pop();
                    const episodeTitle = this.textContent.trim();
                    
                    // Extract anime slug from the URL
                    const animeSlug = card.querySelector('a[href*="detail_anime"]')?.href.split('/').pop() || '';
                    
                    addToWatchHistory(null, title, animeSlug, episodeSlug, episodeTitle, cover);
                }
            }
        });
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Track episode clicks
    trackEpisodeClicks();
    
    // Check if we're on the collection page
    const historyContainer = document.getElementById('history-container');
    if (historyContainer) {
        loadWatchHistory();
    }
    
    // Add event listener to clear history button
    const clearHistoryBtn = document.getElementById('clear-history');
    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener('click', () => {
            if (confirm('Apakah Anda yakin ingin menghapus semua riwayat tontonan?')) {
                clearWatchHistory();
                loadWatchHistory();
                showNotification('Riwayat tontonan telah dihapus');
            }
        });
    }
});

// Export for potential use in other modules
export {
    getWatchHistory,
    addToWatchHistory,
    removeFromHistory,
    clearWatchHistory,
    isInWatchHistory,
    getAnimeWatchHistory,
    loadWatchHistory,
    trackEpisodeClicks
};