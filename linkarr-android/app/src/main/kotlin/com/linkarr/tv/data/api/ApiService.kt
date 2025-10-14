package com.linkarr.tv.data.api

import com.linkarr.tv.data.model.*
import retrofit2.Response
import retrofit2.http.*

/**
 * Linkarr API Service
 * Retrofit interface for backend API communication
 */
interface ApiService {

    // Authentication Endpoints
    @POST("api/auth/register")
    suspend fun register(@Body request: RegisterRequest): Response<UserResponse>

    @FormUrlEncoded
    @POST("api/auth/login")
    suspend fun login(
        @Field("username") username: String,
        @Field("password") password: String
    ): Response<TokenResponse>

    @GET("api/auth/me")
    suspend fun getCurrentUser(): Response<UserResponse>

    @POST("api/auth/rd-token")
    suspend fun storeRdToken(@Body request: RdTokenRequest): Response<UserResponse>

    @DELETE("api/auth/rd-token")
    suspend fun removeRdToken(): Response<Unit>

    // Library Endpoints
    @GET("api/library/stats")
    suspend fun getLibraryStats(): Response<LibraryStats>

    @GET("api/library/movies")
    suspend fun getMovies(
        @Query("page") page: Int = 1,
        @Query("page_size") pageSize: Int = 20,
        @Query("sort_by") sortBy: String = "added_at",
        @Query("sort_order") sortOrder: String = "desc",
        @Query("available_only") availableOnly: Boolean = false
    ): Response<PaginatedResponse>

    @GET("api/library/shows")
    suspend fun getTvShows(
        @Query("page") page: Int = 1,
        @Query("page_size") pageSize: Int = 20,
        @Query("sort_by") sortBy: String = "added_at",
        @Query("sort_order") sortOrder: String = "desc",
        @Query("available_only") availableOnly: Boolean = false
    ): Response<PaginatedResponse>

    @GET("api/library/recent")
    suspend fun getRecentlyAdded(
        @Query("limit") limit: Int = 20,
        @Query("media_type") mediaType: String? = null
    ): Response<List<MediaItemSummary>>

    @GET("api/library/search")
    suspend fun searchLibrary(
        @Query("q") query: String,
        @Query("page") page: Int = 1,
        @Query("page_size") pageSize: Int = 20,
        @Query("media_type") mediaType: String? = null
    ): Response<PaginatedResponse>

    // Media Endpoints
    @GET("api/media/{id}")
    suspend fun getMediaDetails(@Path("id") mediaId: Int): Response<MediaItemDetail>

    @GET("api/media/{id}/seasons")
    suspend fun getMediaSeasons(@Path("id") mediaId: Int): Response<List<SeasonResponse>>

    @GET("api/media/{id}/seasons/{season_number}/episodes")
    suspend fun getSeasonEpisodes(
        @Path("id") mediaId: Int,
        @Path("season_number") seasonNumber: Int
    ): Response<List<EpisodeResponse>>

    @GET("api/media/{id}/play")
    suspend fun getMovieStreamingUrl(@Path("id") mediaId: Int): Response<StreamingUrlResponse>

    @GET("api/media/episodes/{id}/play")
    suspend fun getEpisodeStreamingUrl(@Path("id") episodeId: Int): Response<StreamingUrlResponse>
}
