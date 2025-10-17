package com.linkarr.tv.data.repository

import com.linkarr.tv.data.api.ApiService
import com.linkarr.tv.data.model.*
import com.linkarr.tv.util.Result
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Media Repository
 * Handles media content operations
 */
@Singleton
class MediaRepository @Inject constructor(
    private val apiService: ApiService
) {

    // Library Operations
    suspend fun getLibraryStats(): Result<LibraryStats> {
        return try {
            val response = apiService.getLibraryStats()

            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.message() ?: "Failed to fetch library stats")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error occurred")
        }
    }

    suspend fun getMovies(
        page: Int = 1,
        pageSize: Int = 20,
        sortBy: String = "added_at",
        sortOrder: String = "desc",
        availableOnly: Boolean = false
    ): Result<PaginatedResponse> {
        return try {
            val response = apiService.getMovies(page, pageSize, sortBy, sortOrder, availableOnly)

            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.message() ?: "Failed to fetch movies")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error occurred")
        }
    }

    suspend fun getTvShows(
        page: Int = 1,
        pageSize: Int = 20,
        sortBy: String = "added_at",
        sortOrder: String = "desc",
        availableOnly: Boolean = false
    ): Result<PaginatedResponse> {
        return try {
            val response = apiService.getTvShows(page, pageSize, sortBy, sortOrder, availableOnly)

            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.message() ?: "Failed to fetch TV shows")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error occurred")
        }
    }

    suspend fun getRecentlyAdded(
        limit: Int = 20,
        mediaType: String? = null
    ): Result<List<MediaItemSummary>> {
        return try {
            val response = apiService.getRecentlyAdded(limit, mediaType)

            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.message() ?: "Failed to fetch recent content")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error occurred")
        }
    }

    suspend fun searchLibrary(
        query: String,
        page: Int = 1,
        pageSize: Int = 20,
        mediaType: String? = null
    ): Result<PaginatedResponse> {
        return try {
            val response = apiService.searchLibrary(query, page, pageSize, mediaType)

            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.message() ?: "Failed to search library")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error occurred")
        }
    }

    // Media Details Operations
    suspend fun getMediaDetails(mediaId: Int): Result<MediaItemDetail> {
        return try {
            val response = apiService.getMediaDetails(mediaId)

            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.message() ?: "Failed to fetch media details")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error occurred")
        }
    }

    suspend fun getMediaSeasons(mediaId: Int): Result<List<SeasonResponse>> {
        return try {
            val response = apiService.getMediaSeasons(mediaId)

            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.message() ?: "Failed to fetch seasons")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error occurred")
        }
    }

    suspend fun getSeasonEpisodes(
        mediaId: Int,
        seasonNumber: Int
    ): Result<List<EpisodeResponse>> {
        return try {
            val response = apiService.getSeasonEpisodes(mediaId, seasonNumber)

            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.message() ?: "Failed to fetch episodes")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error occurred")
        }
    }

    // Streaming Operations
    suspend fun getMovieStreamingUrl(mediaId: Int): Result<StreamingUrlResponse> {
        return try {
            val response = apiService.getMovieStreamingUrl(mediaId)

            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.message() ?: "Failed to get streaming URL")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error occurred")
        }
    }

    suspend fun getEpisodeStreamingUrl(episodeId: Int): Result<StreamingUrlResponse> {
        return try {
            val response = apiService.getEpisodeStreamingUrl(episodeId)

            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.message() ?: "Failed to get streaming URL")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error occurred")
        }
    }
}
