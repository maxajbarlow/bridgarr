package com.linkarr.tv.ui.screens.home

import androidx.compose.foundation.layout.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import androidx.tv.material3.*

/**
 * Home Screen
 * Displays media library navigation and content carousels
 */
@OptIn(ExperimentalTvMaterial3Api::class)
@Composable
fun HomeScreen(
    navController: NavController
) {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp),
            modifier = Modifier.padding(48.dp)
        ) {
            Text(
                text = "Linkarr Home",
                style = MaterialTheme.typography.displayMedium
            )

            Text(
                text = "v0.1.0-build.1",
                style = MaterialTheme.typography.bodyMedium
            )

            Spacer(modifier = Modifier.height(32.dp))

            Row(
                horizontalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Button(onClick = { /* Navigate to Movies */ }) {
                    Text("Movies")
                }

                Button(onClick = { /* Navigate to TV Shows */ }) {
                    Text("TV Shows")
                }

                Button(onClick = { /* Navigate to Search */ }) {
                    Text("Search")
                }

                Button(onClick = { /* Navigate to Settings */ }) {
                    Text("Settings")
                }
            }
        }
    }
}
