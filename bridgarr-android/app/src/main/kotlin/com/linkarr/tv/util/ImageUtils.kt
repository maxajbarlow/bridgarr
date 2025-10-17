package com.linkarr.tv.util

/**
 * Image utility functions for TMDb images
 */
object ImageUtils {

    /**
     * Get full poster URL from TMDb path
     */
    fun getPosterUrl(posterPath: String?, size: String = Constants.POSTER_SIZE_W500): String? {
        return posterPath?.let {
            "${Constants.TMDB_IMAGE_BASE_URL}${size}${it}"
        }
    }

    /**
     * Get full backdrop URL from TMDb path
     */
    fun getBackdropUrl(backdropPath: String?, size: String = Constants.BACKDROP_SIZE_W1280): String? {
        return backdropPath?.let {
            "${Constants.TMDB_IMAGE_BASE_URL}${size}${it}"
        }
    }

    /**
     * Get full episode still URL from TMDb path
     */
    fun getStillUrl(stillPath: String?, size: String = Constants.STILL_SIZE_W300): String? {
        return stillPath?.let {
            "${Constants.TMDB_IMAGE_BASE_URL}${size}${it}"
        }
    }

    /**
     * Get placeholder image URL for missing posters
     */
    fun getPlaceholderUrl(): String {
        return "https://via.placeholder.com/500x750.png?text=No+Poster"
    }
}
