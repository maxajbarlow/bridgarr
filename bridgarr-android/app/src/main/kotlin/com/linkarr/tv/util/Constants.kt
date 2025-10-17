package com.linkarr.tv.util

/**
 * Application Constants
 */
object Constants {
    // API Configuration
    const val DEFAULT_BASE_URL = "http://10.0.2.2:8000/"  // Android emulator localhost
    const val CONNECT_TIMEOUT = 30L  // seconds
    const val READ_TIMEOUT = 30L     // seconds
    const val WRITE_TIMEOUT = 30L    // seconds

    // TMDb Image Configuration
    const val TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/"
    const val POSTER_SIZE_W500 = "w500"
    const val BACKDROP_SIZE_W1280 = "w1280"
    const val STILL_SIZE_W300 = "w300"

    // Pagination
    const val DEFAULT_PAGE_SIZE = 20
    const val INITIAL_PAGE = 1

    // Media Types
    const val MEDIA_TYPE_MOVIE = "movie"
    const val MEDIA_TYPE_TV_SHOW = "tv_show"

    // Sort Options
    const val SORT_BY_ADDED_AT = "added_at"
    const val SORT_BY_TITLE = "title"
    const val SORT_BY_RELEASE_DATE = "release_date"
    const val SORT_BY_VOTE_AVERAGE = "vote_average"

    const val SORT_ORDER_ASC = "asc"
    const val SORT_ORDER_DESC = "desc"

    // UI Configuration
    const val GRID_COLUMNS = 4
    const val FOCUS_SCALE = 1.1f
    const val ANIMATION_DURATION = 300
}
