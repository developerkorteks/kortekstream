/**
 * Watch History functionality for KortekStream
 * Handles storing and retrieving anime watch history data in localStorage
 * Now supports dynamic APIs and multiple sources
 */

// Constants
const STORAGE_KEY = 'kortekstream_history';
const MAX_HISTORY_ITEMS = 100;

/**
 * Get current API source information
 * @returns {Object} Current API source info
 */
async function getCurrentAPISource() {
    try {
        // Try to get from Django context if available
        if (typeof window.currentAPISource !== 'undefined') {
            return window.currentAPISource;
        }
        
        // Fallback to default
        return {
            name: 'Default API',
            domain: 'gomunime.co',
            endpoint: 'https://api.gomunime.co/api/v1'
        };
    } catch (error) {
        console.error('Error getting current API source:', error);
        return {
            name: 'Default API',
            domain: 'gomunime.co',
            endpoint: 'https://api.gomunime.co/api/v1'
        };
    }
}

/**
 * Normalize episode slug for different API sources
 * @param {string} episodeSlug - Raw episode slug
 * @param {string} sourceDomain - Source domain
 * @returns {string} Normalized episode slug
 */
function normalizeEpisodeSlug(episodeSlug, sourceDomain = null) {
    if (!episodeSlug) return '';
    
    let normalized = episodeSlug;
    
    // Remove protocol and domain if present
    normalized = normalized.replace(/^https?:\/\/[^\/]+\//, '');
    
    // Remove episode prefix if present
    normalized = normalized.replace(/^\/?episode\//, '');
    
    // Handle specific domain formats
    if (sourceDomain) {
        const domainRegex = new RegExp(`^${sourceDomain.replace(/\./g, '\\.')}\/?`, 'i');
        normalized = normalized.replace(domainRegex, '');
    }
    
    // Handle common URL patterns
    normalized = normalized.replace(/^https:[^/]+/, ''); // Handle malformed URLs
    
    // Remove trailing slash
    normalized = normalized.replace(/\/$/, '');
    
    return normalized;
}

/**
 * Build episode URL for current API source
 * @param {string} episodeSlug - Episode slug
 * @param {string} sourceDomain - Source domain
 * @returns {string} Complete episode URL
 */
function buildEpisodeURL(episodeSlug, sourceDomain = null) {
    if (!episodeSlug) return '';
    
    const normalizedSlug = normalizeEpisodeSlug(episodeSlug, sourceDomain);
    
    if (!sourceDomain) {
        // Try to get from current API source
        return `/episode/${normalizedSlug}`;
    }
    
    // Ensure domain doesn't have protocol
    const cleanDomain = sourceDomain.replace(/^https?:\/\//, '');
    
    return `https://${cleanDomain}/${normalizedSlug}`;
}

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
 * Add anime to watch history with dynamic API support
 * @param {number|null} animeId - Anime ID (optional)
 * @param {string} title - Anime title
 * @param {string} slug - Anime slug
 * @param {string} episodeSlug - Episode slug
 * @param {string} episodeTitle - Episode title
 * @param {string} cover - Anime cover image URL
 * @param {Object} apiSource - API source information (optional)
 * @returns {boolean} Success status
 */
async function addToWatchHistory(animeId, title, slug, episodeSlug, episodeTitle, cover, apiSource = null) {
    try {
        console.log("addToWatchHistory dipanggil dengan:", {
            title, slug, episodeSlug, episodeTitle,
            cover: cover ? (cover.length > 30 ? cover.substring(0, 30) + '...' : cover) : 'undefined',
            apiSource
        });
        
        // Get current API source if not provided
        if (!apiSource) {
            apiSource = await getCurrentAPISource();
        }
        
        let history = getWatchHistory();
        
        // Limit history to MAX_HISTORY_ITEMS items
        if (history.length >= MAX_HISTORY_ITEMS) {
            history = history.slice(0, MAX_HISTORY_ITEMS - 1);
        }
        
        // Normalize slugs for better matching
        const normalizedEpisodeSlug = normalizeEpisodeSlug(episodeSlug, apiSource.domain);
        const normalizedAnimeSlug = normalizeEpisodeSlug(slug, apiSource.domain);
        
        console.log("Slugs dinormalisasi:", {
            original: { episodeSlug, slug },
            normalized: { episodeSlug: normalizedEpisodeSlug, slug: normalizedAnimeSlug }
        });
        
        // Check for existing entries with same episode slug (after normalization)
        const existingIndex = history.findIndex(item => {
            const itemEpisodeSlug = normalizeEpisodeSlug(item.episodeSlug, item.apiSource?.domain);
            return itemEpisodeSlug === normalizedEpisodeSlug;
        });
        
        if (existingIndex !== -1) {
            console.log("Entri sudah ada di indeks", existingIndex, "dengan episodeSlug", history[existingIndex].episodeSlug);
            // Remove existing entry
            history.splice(existingIndex, 1);
        }
        
        // Validate and fix cover URL
        if (!cover || cover === "undefined" || cover === "N/A" || cover === "-" || cover === "" || cover === "null") {
            console.log("Cover tidak valid, menggunakan default");
            cover = "/static/img/kortekstream-logo.png";
        }
        
        // Ensure cover URL is valid
        if (cover && !cover.startsWith('http') && !cover.startsWith('/')) {
            console.log("URL cover tidak valid, menggunakan default:", cover);
            cover = "/static/img/kortekstream-logo.png";
        }
        
        // Fix malformed cover URLs
        if (cover && cover.startsWith('https:v1.samehadaku.how')) {
            console.log("Format URL cover tidak valid, memperbaiki:", cover);
            cover = cover.replace('https:v1.samehadaku.how', 'https://v1.samehadaku.how');
        }
        
        // Use kortekstream-logo.png instead of logo.png
        if (cover === "/static/img/logo.png") {
            console.log("Menggunakan kortekstream-logo.png sebagai pengganti logo.png");
            cover = "/static/img/kortekstream-logo.png";
        }
        
        // Add to beginning of array (most recent first)
        const historyItem = {
            id: animeId || Date.now(),
            title: title || "Anime Tidak Diketahui",
            slug: normalizedAnimeSlug,
            episodeSlug: normalizedEpisodeSlug,
            episodeTitle: episodeTitle || "Episode Tidak Diketahui",
            cover: cover,
            watchedAt: new Date().toISOString(),
            apiSource: {
                name: apiSource.name || 'Unknown API',
                domain: apiSource.domain || 'unknown',
                endpoint: apiSource.endpoint || 'unknown'
            }
        };
        
        history.unshift(historyItem);
        
        // Deduplicate history based on normalized episode slug
        const uniqueHistory = [];
        const seenEpisodeSlugs = new Set();
        
        for (const item of history) {
            const normalizedItemSlug = normalizeEpisodeSlug(item.episodeSlug, item.apiSource?.domain);
            if (!seenEpisodeSlugs.has(normalizedItemSlug)) {
                seenEpisodeSlugs.add(normalizedItemSlug);
                uniqueHistory.push(item);
            }
        }
        
        console.log(`Deduplikasi: ${history.length} item -> ${uniqueHistory.length} item unik`);
        
        localStorage.setItem(STORAGE_KEY, JSON.stringify(uniqueHistory));
        console.log("Riwayat disimpan, jumlah item:", uniqueHistory.length);
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
 * Load watch history into container with dynamic API support
 * @param {string} containerId - ID of container element
 */
async function loadWatchHistoryToEpisode(containerId = 'history-container') {
    console.log("Memuat riwayat tontonan dengan dukungan API dinamis");
    
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const history = getWatchHistory();
    
    // Log untuk memverifikasi data riwayat
    if (history.length > 0) {
        console.log("Contoh item riwayat pertama:", {
            title: history[0].title,
            slug: history[0].slug,
            episodeSlug: history[0].episodeSlug,
            apiSource: history[0].apiSource,
            linkDetailEpisode: `/episode/${history[0].episodeSlug}`
        });
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
    for (const item of history) {
        // Build episode URL using current API source
        const episodeURL = buildEpisodeURL(item.episodeSlug, item.apiSource?.domain);
        
        // Verify and fix cover URL
        let coverUrl = item.cover;
        if (!coverUrl || coverUrl === "undefined" || coverUrl === "N/A" || coverUrl === "-" || coverUrl === "" || coverUrl === "null") {
            coverUrl = "/static/img/kortekstream-logo.png";
        }
        
        // Ensure cover URL is valid
        if (coverUrl && !coverUrl.startsWith('http') && !coverUrl.startsWith('/')) {
            coverUrl = "/static/img/kortekstream-logo.png";
        }
        
        // Fix malformed cover URLs
        if (coverUrl && coverUrl.startsWith('https:v1.samehadaku.how')) {
            coverUrl = coverUrl.replace('https:v1.samehadaku.how', 'https://v1.samehadaku.how');
        }
        
        // Use kortekstream-logo.png instead of logo.png
        if (coverUrl === "/static/img/logo.png") {
            coverUrl = "/static/img/kortekstream-logo.png";
        }
        
        html += `
            <div class="anime-card dynamic-border bg-white dark:bg-darkSecondary rounded-lg overflow-hidden shadow-md hover:shadow-lg transition-all duration-300 border border-gray-200 dark:border-gray-700">
                <a href="${episodeURL}" class="block"
                   onclick="console.log('Navigasi riwayat ke episode: ' + (this.href || window.location.origin + '${episodeURL}'))">
                    <div class="relative pb-[140%] overflow-hidden">
                        <img src="${coverUrl}" alt="${item.title}" class="absolute inset-0 w-full h-full object-cover transition-transform duration-300 hover:scale-105" onerror="this.src='/static/img/kortekstream-logo.png'; console.log('Gambar sampul gagal dimuat, menggunakan default:', this.alt);">
                        
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
                            <a href="/anime/${item.slug}" class="text-primary dark:text-darkPrimary hover:underline">
                                <i class="fas fa-info-circle mr-1"></i>Detail Anime
                            </a>
                        </div>
                        ${item.apiSource ? `<div class="text-xs text-gray-400 mt-1">Sumber: ${item.apiSource.name}</div>` : ''}
                    </div>
                </a>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// Fungsi asli untuk kompatibilitas
function loadWatchHistory(containerId = 'history-container') {
    // Gunakan fungsi baru untuk mengarahkan ke detail episode
    return loadWatchHistoryToEpisode(containerId);
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
 * Track episode clicks to add to watch history with dynamic API support
 */
async function trackEpisodeClicks() {
    // Update selector to include new URL format
    const episodeLinks = document.querySelectorAll('a[href*="detail_episode_video"], a[href*="episode/"]');
    
    episodeLinks.forEach(link => {
        link.addEventListener('click', async function(e) {
            // Get anime info from closest parent
            const card = this.closest('.anime-card');
            if (card) {
                const titleEl = card.querySelector('.title');
                const coverEl = card.querySelector('img');
                
                if (titleEl && coverEl) {
                    const title = titleEl.textContent.trim();
                    const cover = coverEl.src;
                    const href = this.getAttribute('href');
                    
                    // Extract episodeSlug from URL
                    let episodeSlug;
                    if (href.includes('detail_episode_video')) {
                        // Old URL format
                        episodeSlug = href.split('/').pop();
                    } else if (href.includes('episode/')) {
                        // New URL format
                        episodeSlug = href.replace(/^.*episode\//, '').replace(/\/$/, '');
                    } else {
                        episodeSlug = href.split('/').pop();
                    }
                    
                    const episodeTitle = this.textContent.trim();
                    
                    // Extract anime slug from the URL
                    const animeLink = card.querySelector('a[href*="anime"], a[href*="detail_anime"]');
                    let animeSlug = '';
                    
                    if (animeLink) {
                        const animeHref = animeLink.href;
                        if (animeHref.includes('anime/')) {
                            animeSlug = animeHref.replace(/^.*anime\//, '').replace(/\/$/, '');
                        } else if (animeHref.includes('detail_anime/')) {
                            animeSlug = animeHref.replace(/^.*detail_anime\//, '').replace(/\/$/, '');
                        }
                    }
                    
                    // Get current API source
                    const apiSource = await getCurrentAPISource();
                    
                    console.log(`Menambahkan ke riwayat tontonan: ${episodeTitle} (${episodeSlug}), anime: ${animeSlug}, API: ${apiSource.name}`);
                    await addToWatchHistory(null, title, animeSlug, episodeSlug, episodeTitle, cover, apiSource);
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
    trackEpisodeClicks,
    getCurrentAPISource,
    normalizeEpisodeSlug,
    buildEpisodeURL
};