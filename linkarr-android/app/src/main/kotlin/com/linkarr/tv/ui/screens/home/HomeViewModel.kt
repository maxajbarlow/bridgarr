package com.linkarr.tv.ui.screens.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.linkarr.tv.data.model.LibraryStats
import com.linkarr.tv.data.model.MediaItemSummary
import com.linkarr.tv.data.repository.AuthRepository
import com.linkarr.tv.data.repository.MediaRepository
import com.linkarr.tv.util.Result
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * ViewModel for Home Screen
 */
@HiltViewModel
class HomeViewModel @Inject constructor(
    private val mediaRepository: MediaRepository,
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<HomeUiState>(HomeUiState.Loading)
    val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()

    private val _username = MutableStateFlow<String?>(null)
    val username: StateFlow<String?> = _username.asStateFlow()

    init {
        loadHomeData()
        loadUsername()
    }

    private fun loadUsername() {
        viewModelScope.launch {
            authRepository.usernameFlow.collect { username ->
                _username.value = username
            }
        }
    }

    fun loadHomeData() {
        viewModelScope.launch {
            _uiState.value = HomeUiState.Loading

            // Load library stats
            val statsResult = mediaRepository.getLibraryStats()

            // Load recently added content
            val recentResult = mediaRepository.getRecentlyAdded(limit = 20)

            // Load featured movies
            val moviesResult = mediaRepository.getMovies(page = 1, pageSize = 10)

            // Load featured TV shows
            val showsResult = mediaRepository.getTvShows(page = 1, pageSize = 10)

            if (statsResult is Result.Success &&
                recentResult is Result.Success &&
                moviesResult is Result.Success &&
                showsResult is Result.Success
            ) {
                _uiState.value = HomeUiState.Success(
                    stats = statsResult.data,
                    recentlyAdded = recentResult.data,
                    featuredMovies = moviesResult.data.items,
                    featuredShows = showsResult.data.items
                )
            } else {
                val errorMessage = (statsResult as? Result.Error)?.message
                    ?: (recentResult as? Result.Error)?.message
                    ?: (moviesResult as? Result.Error)?.message
                    ?: (showsResult as? Result.Error)?.message
                    ?: "Failed to load home data"

                _uiState.value = HomeUiState.Error(errorMessage)
            }
        }
    }

    fun logout() {
        viewModelScope.launch {
            authRepository.logout()
        }
    }
}

sealed class HomeUiState {
    object Loading : HomeUiState()
    data class Success(
        val stats: LibraryStats,
        val recentlyAdded: List<MediaItemSummary>,
        val featuredMovies: List<MediaItemSummary>,
        val featuredShows: List<MediaItemSummary>
    ) : HomeUiState()
    data class Error(val message: String) : HomeUiState()
}
