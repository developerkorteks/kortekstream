/**
 * Favorites functionality for KortekStream
 * Handles storing and retrieving anime favorites data in localStorage
 */

// Constants
const STORAGE_KEY = 'kortekstream_favorites';

/**
 * Get favorites from localStorage
 * @returns {Array} Array of favorite items
 */
function getFavorites() {
    try {
        const favorites = localStorage.getItem(STORAGE_KEY);
        return favorites ? JSON.parse(favorites) : [];
    } catch (error) {
        console.error('Error getting favorites:', error);
        return [];
    }
}

/**
 * Add anime to favorites
 * @param {number|null} animeId - Anime ID (optional)
 * @param {string} title - Anime title
 * @param {string} slug - Anime slug
 * @param {string} cover - Anime cover image URL
 * @returns {boolean} Success status
 */
function addToFavorites(animeId, title, slug, cover) {
    try {
        const favorites = getFavorites();
        
        // Check if anime is already in favorites
        if (!favorites.some(item => item.slug === slug)) {
            favorites.push({
                id: animeId || Date.now(),
                title: title,
                slug: slug,
                cover: cover,
                addedAt: new Date().toISOString()
            });
            
            localStorage.setItem(STORAGE_KEY, JSON.stringify(favorites));
            return true;
        }
        return false;
    } catch (error) {
        console.error('Error adding to favorites:', error);
        return false;
    }
}

/**
 * Remove anime from favorites
 * @param {string} slug - Anime slug
 * @returns {boolean} Success status
 */
function removeFromFavorites(slug) {
    try {
        let favorites = getFavorites();
        favorites = favorites.filter(item => item.slug !== slug);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(favorites));
        return true;
    } catch (error) {
        console.error('Error removing from favorites:', error);
        return false;
    }
}

/**
 * Check if anime is in favorites
 * @param {string} slug - Anime slug
 * @returns {boolean} True if anime is in favorites
 */
function isInFavorites(slug) {
    const favorites = getFavorites();
    return favorites.some(item => item.slug === slug);
}

/**
 * Clear entire favorites list
 * @returns {boolean} Success status
 */
function clearFavorites() {
    try {
        localStorage.removeItem(STORAGE_KEY);
        return true;
    } catch (error) {
        console.error('Error clearing favorites:', error);
        return false;
    }
}

/**
 * Update favorites UI elements
 * @param {string} slug - Anime slug
 * @param {boolean|null} isAdded - Whether anime is added (null to check)
 */
function updateFavoriteUI(slug, isAdded = null) {
    // Find favorite button
    const btn = document.getElementById('favorite-btn');
    const icon = document.getElementById('favorite-icon');
    const text = document.getElementById('favorite-text');
    
    if (!btn || !icon || !text) return;
    
    const inFavorites = isAdded !== null ? isAdded : isInFavorites(slug);
    
    if (inFavorites) {
        btn.classList.remove('bg-black/50');
        btn.classList.add('bg-red-500/80');
        icon.classList.remove('far', 'fa-heart');
        icon.classList.add('fas', 'fa-heart');
        text.textContent = 'Favorit';
    } else {
        btn.classList.remove('bg-red-500/80');
        btn.classList.add('bg-black/50');
        icon.classList.remove('fas', 'fa-heart');
        icon.classList.add('far', 'fa-heart');
        text.textContent = 'Favorit';
    }
}

/**
 * Toggle anime in favorites
 * @param {string} title - Anime title
 * @param {string} slug - Anime slug
 * @param {string} cover - Anime cover image URL
 * @returns {boolean} New favorites status
 */
function toggleFavorite(title, slug, cover) {
    const inFavorites = isInFavorites(slug);
    
    if (inFavorites) {
        removeFromFavorites(slug);
        updateFavoriteUI(slug, false);
        showNotification('Dihapus dari favorit');
        return false;
    } else {
        addToFavorites(null, title, slug, cover);
        updateFavoriteUI(slug, true);
        showNotification('Ditambahkan ke favorit');
        return true;
    }
}

/**
 * Load favorites into container
 * @param {string} containerId - ID of container element
 */
function loadFavorites(containerId = 'favorites-container') {
    // Log untuk verifikasi perubahan
    console.log("Memuat favorit dengan link ke detail anime");
    
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const favorites = getFavorites();
    
    // Log untuk memverifikasi data favorit
    if (favorites.length > 0) {
        console.log("Contoh item favorit pertama:", {
            title: favorites[0].title,
            slug: favorites[0].slug,
            linkDetailAnime: `/anime/${favorites[0].slug}`
        });
    }
    
    if (favorites.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12 col-span-full">
                <i class="fas fa-heart text-gray-300 dark:text-gray-600 text-5xl mb-4"></i>
                <p class="text-gray-500 dark:text-gray-400">Daftar favorit Anda kosong</p>
                <p class="text-gray-500 dark:text-gray-400 text-sm mt-2">Tambahkan anime ke favorit dengan mengklik tombol "Favorit" di halaman detail anime</p>
            </div>
        `;
        return;
    }
    
    // Sort by added date (newest first)
    favorites.sort((a, b) => new Date(b.addedAt) - new Date(a.addedAt));
    
    let html = '';
    favorites.forEach(item => {
        html += `
            <div class="anime-card dynamic-border bg-white dark:bg-darkSecondary rounded-lg overflow-hidden shadow-md hover:shadow-lg transition-all duration-300 border border-gray-200 dark:border-gray-700">
                <a href="${item.slug.includes('/anime/') ? item.slug : `/anime/${item.slug}`}" class="block"
                   onclick="console.log('Navigasi ke: ' + (this.href || window.location.origin + (item.slug.includes('/anime/') ? item.slug : '/anime/' + item.slug)))">
                    <div class="relative pb-[140%] overflow-hidden">
                        <img src="${item.cover}" alt="${item.title}" class="absolute inset-0 w-full h-full object-cover transition-transform duration-300 hover:scale-105">
                        
                        <div class="absolute top-2 right-2 bg-red-500 text-white text-xs font-bold px-2 py-1 rounded-md">
                            <i class="fas fa-heart mr-1"></i> Favorit
                        </div>
                        
                        <button onclick="event.preventDefault(); removeFromFavoritesAndUpdate('${item.slug}')" class="absolute bottom-2 right-2 bg-red-500 text-white w-8 h-8 rounded-full flex items-center justify-center hover:bg-red-600 transition-colors dark:bg-red-600 dark:hover:bg-red-700">
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
 * Remove from favorites and update UI
 * @param {string} slug - Anime slug
 */
function removeFromFavoritesAndUpdate(slug) {
    removeFromFavorites(slug);
    loadFavorites();
    showNotification('Dihapus dari favorit');
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
    const favoriteBtn = document.getElementById('favorite-btn');
    
    if (favoriteBtn && animeSlug) {
        updateFavoriteUI(animeSlug);
    }
    
    // Check if we're on the collection page
    const favoritesContainer = document.getElementById('favorites-container');
    if (favoritesContainer) {
        loadFavorites();
    }
});

// Export for potential use in other modules
export {
    getFavorites,
    addToFavorites,
    removeFromFavorites,
    isInFavorites,
    clearFavorites,
    toggleFavorite,
    loadFavorites,
    updateFavoriteUI
};