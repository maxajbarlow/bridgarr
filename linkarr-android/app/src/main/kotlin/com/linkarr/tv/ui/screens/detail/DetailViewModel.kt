package com.linkarr.tv.ui.screens.detail

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.linkarr.tv.data.model.*
import com.linkarr.tv.data.repository.MediaRepository
import com.linkarr.tv.util.Result
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * ViewModel for Media Detail Screen
 */
@HiltViewModel
class DetailViewModel @Inject constructor(
    private val mediaRepository: MediaRepository,
    savedStateHandle: SavedStateHandle
) : ViewModel() {

    private val mediaId: Int = checkNotNull(savedStateHandle["mediaId"])

    private val _uiState = MutableStateFlow<DetailUiState>(DetailUiState.Loading)
    val uiState: StateFlow<DetailUiState> = _uiState.asStateFlow()

    init {
        loadMediaDetails()
    }

    private fun loadMediaDetails() {
        viewModelScope.launch {
            _uiState.value = DetailUiState.Loading

            val detailsResult = mediaRepository.getMediaDetails(mediaId)

            if (detailsResult is Result.Success) {
                val details = detailsResult.data

                // If TV show, load seasons
                if (details.mediaType == "tv_show") {
                    val seasonsResult = mediaRepository.getMediaSeasons(mediaId)

                    if (seasonsResult is Result.Success) {
                        _uiState.value = DetailUiState.Success(
                            details = details,
                            seasons = seasonsResult.data
                        )
                    } else {
                        _uiState.value = DetailUiState.Error(
                            seasonsResult.getErrorOrNull() ?: "Failed to load seasons"
                        )
                    }
                } else {
                    _uiState.value = DetailUiState.Success(
                        details = details,
                        seasons = emptyList()
                    )
                }
            } else {
                _uiState.value = DetailUiState.Error(
                    detailsResult.getErrorOrNull() ?: "Failed to load details"
                )
            }
        }
    }

    fun loadSeasonEpisodes(seasonNumber: Int) {
        viewModelScope.launch {
            val episodesResult = mediaRepository.getSeasonEpisodes(mediaId, seasonNumber)

            if (episodesResult is Result.Success) {
                val currentState = _uiState.value
                if (currentState is DetailUiState.Success) {
                    _uiState.value = currentState.copy(
                        selectedSeasonEpisodes = episodesResult.data,
                        selectedSeasonNumber = seasonNumber
                    )
                }
            }
        }
    }

    fun getStreamingUrl(episodeId: Int? = null) {
        viewModelScope.launch {
            val result = if (episodeId != null) {
                mediaRepository.getEpisodeStreamingUrl(episodeId)
            } else {
                mediaRepository.getMovieStreamingUrl(mediaId)
            }

            if (result is Result.Success) {
                val currentState = _uiState.value
                if (currentState is DetailUiState.Success) {
                    _uiState.value = currentState.copy(
                        streamingUrl = result.data
                    )
                }
            }
        }
    }
}

sealed class DetailUiState {
    object Loading : DetailUiState()
    data class Success(
        val details: MediaItemDetail,
        val seasons: List<SeasonResponse>,
        val selectedSeasonNumber: Int? = null,
        val selectedSeasonEpisodes: List<EpisodeResponse> = emptyList(),
        val streamingUrl: StreamingUrlResponse? = null
    ) : DetailUiState()
    data class Error(val message: String) : DetailUiState()
}
