package com.linkarr.tv.data.model

import com.google.gson.annotations.SerializedName
import java.util.Date

/**
 * API Data Models
 * DTOs for API communication
 */

// Authentication Models
data class RegisterRequest(
    val username: String,
    val email: String,
    val password: String
)

data class TokenResponse(
    @SerializedName("access_token")
    val accessToken: String,
    @SerializedName("token_type")
    val tokenType: String = "bearer"
)

data class UserResponse(
    val id: Int,
    val username: String,
    val email: String,
    @SerializedName("is_active")
    val isActive: Boolean,
    @SerializedName("is_admin")
    val isAdmin: Boolean,
    @SerializedName("has_rd_token")
    val hasRdToken: Boolean,
    @SerializedName("created_at")
    val createdAt: String
)

data class RdTokenRequest(
    @SerializedName("rd_api_token")
    val rdApiToken: String
)

// Library Models
data class LibraryStats(
    @SerializedName("total_movies")
    val totalMovies: Int,
    @SerializedName("total_shows")
    val totalShows: Int,
    @SerializedName("total_episodes")
    val totalEpisodes: Int,
    @SerializedName("available_movies")
    val availableMovies: Int,
    @SerializedName("available_shows")
    val availableShows: Int
)

data class MediaItemSummary(
    val id: Int,
    @SerializedName("tmdb_id")
    val tmdbId: Int,
    @SerializedName("imdb_id")
    val imdbId: String?,
    val title: String,
    @SerializedName("media_type")
    val mediaType: String,
    @SerializedName("release_date")
    val releaseDate: String?,
    @SerializedName("poster_path")
    val posterPath: String?,
    @SerializedName("backdrop_path")
    val backdropPath: String?,
    @SerializedName("vote_average")
    val voteAverage: Float?,
    @SerializedName("is_available")
    val isAvailable: Boolean,
    @SerializedName("added_at")
    val addedAt: String
)

data class PaginatedResponse(
    val items: List<MediaItemSummary>,
    val total: Int,
    val page: Int,
    @SerializedName("page_size")
    val pageSize: Int,
    @SerializedName("total_pages")
    val totalPages: Int
)

// Media Models
data class MediaItemDetail(
    val id: Int,
    @SerializedName("tmdb_id")
    val tmdbId: Int,
    @SerializedName("imdb_id")
    val imdbId: String?,
    val title: String,
    @SerializedName("media_type")
    val mediaType: String,
    val overview: String?,
    @SerializedName("release_date")
    val releaseDate: String?,
    @SerializedName("poster_path")
    val posterPath: String?,
    @SerializedName("backdrop_path")
    val backdropPath: String?,
    @SerializedName("vote_average")
    val voteAverage: Float?,
    @SerializedName("vote_count")
    val voteCount: Int?,
    val runtime: Int?,
    val genres: String?,
    @SerializedName("is_available")
    val isAvailable: Boolean,
    @SerializedName("season_count")
    val seasonCount: Int?
)

data class SeasonResponse(
    val id: Int,
    @SerializedName("season_number")
    val seasonNumber: Int,
    @SerializedName("episode_count")
    val episodeCount: Int,
    val name: String?,
    val overview: String?,
    @SerializedName("poster_path")
    val posterPath: String?,
    @SerializedName("air_date")
    val airDate: String?
)

data class EpisodeResponse(
    val id: Int,
    @SerializedName("episode_number")
    val episodeNumber: Int,
    val name: String?,
    val overview: String?,
    @SerializedName("still_path")
    val stillPath: String?,
    @SerializedName("air_date")
    val airDate: String?,
    val runtime: Int?,
    @SerializedName("has_streaming_url")
    val hasStreamingUrl: Boolean
)

data class StreamingUrlResponse(
    @SerializedName("streaming_url")
    val streamingUrl: String,
    val quality: String?,
    @SerializedName("expires_at")
    val expiresAt: String,
    @SerializedName("media_id")
    val mediaId: Int,
    @SerializedName("episode_id")
    val episodeId: Int?
)

// Error Response
data class ErrorResponse(
    val detail: String
)
