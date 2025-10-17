package com.linkarr.tv.ui.screens.detail

import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.tv.material3.*

/**
 * Media Detail Screen
 * Shows detailed information about a movie or TV show
 */
@OptIn(ExperimentalTvMaterial3Api::class)
@Composable
fun DetailScreen(
    viewModel: DetailViewModel = hiltViewModel(),
    onPlayClick: (mediaId: Int, episodeId: Int?) -> Unit,
    onBackPress: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()

    Surface(
        modifier = Modifier.fillMaxSize(),
        colors = SurfaceDefaults.colors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        when (val state = uiState) {
            is DetailUiState.Loading -> {
                LoadingState()
            }
            is DetailUiState.Success -> {
                DetailContent(
                    state = state,
                    onPlayClick = { episodeId ->
                        onPlayClick(state.details.id, episodeId)
                    },
                    onSeasonSelect = { seasonNumber ->
                        viewModel.loadSeasonEpisodes(seasonNumber)
                    },
                    onBackPress = onBackPress
                )
            }
            is DetailUiState.Error -> {
                ErrorState(
                    message = state.message,
                    onRetry = { /* viewModel.loadMediaDetails() */ }
                )
            }
        }
    }
}

@Composable
private fun LoadingState() {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Text(text = "Loading...")
    }
}

@OptIn(ExperimentalTvMaterial3Api::class)
@Composable
private fun DetailContent(
    state: DetailUiState.Success,
    onPlayClick: (episodeId: Int?) -> Unit,
    onSeasonSelect: (seasonNumber: Int) -> Unit,
    onBackPress: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(48.dp)
    ) {
        // Title
        Text(
            text = state.details.title,
            style = MaterialTheme.typography.headlineLarge,
            color = MaterialTheme.colorScheme.onSurface
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Metadata
        Row(
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            state.details.releaseDate?.let { releaseDate ->
                Text(
                    text = releaseDate.take(4), // Show year
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            state.details.runtime?.let { runtime ->
                Text(
                    text = "$runtime min",
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            state.details.voteAverage?.let { rating ->
                Text(
                    text = "★ ${String.format("%.1f", rating)}",
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Overview
        state.details.overview?.let { overview ->
            Text(
                text = overview,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurface,
                maxLines = 4
            )
        }

        Spacer(modifier = Modifier.height(32.dp))

        // Play Button or Season Selection
        if (state.details.mediaType == "movie") {
            Button(
                onClick = { onPlayClick(null) },
                enabled = state.details.isAvailable
            ) {
                Text(
                    text = if (state.details.isAvailable) "Play Movie" else "Not Available",
                    style = MaterialTheme.typography.labelLarge
                )
            }
        } else {
            // TV Show - Show seasons
            Text(
                text = "Seasons",
                style = MaterialTheme.typography.titleLarge,
                color = MaterialTheme.colorScheme.onSurface
            )

            Spacer(modifier = Modifier.height(16.dp))

            // Season selector
            if (state.seasons.isNotEmpty()) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    state.seasons.forEach { season ->
                        Button(
                            onClick = { onSeasonSelect(season.seasonNumber) }
                        ) {
                            Text(text = "Season ${season.seasonNumber}")
                        }
                    }
                }
            }

            // Episodes list
            if (state.selectedSeasonEpisodes.isNotEmpty()) {
                Spacer(modifier = Modifier.height(24.dp))

                Text(
                    text = "Episodes",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSurface
                )

                Spacer(modifier = Modifier.height(8.dp))

                Column(
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    state.selectedSeasonEpisodes.forEach { episode ->
                        Button(
                            onClick = { onPlayClick(episode.id) },
                            enabled = episode.hasStreamingUrl
                        ) {
                            Text(
                                text = "${episode.episodeNumber}. ${episode.name ?: "Episode ${episode.episodeNumber}"}",
                                maxLines = 1
                            )
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Back Button
        Button(
            onClick = onBackPress
        ) {
            Text(text = "Back")
        }
    }
}

@Composable
private fun ErrorState(
    message: String,
    onRetry: () -> Unit
) {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Text(
                text = "Error: $message",
                color = MaterialTheme.colorScheme.error
            )
            Button(onClick = onRetry) {
                Text(text = "Retry")
            }
        }
    }
}
