package com.linkarr.tv.ui.screens.login

import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.tv.material3.*

/**
 * Login Screen
 * Handles user authentication and Real-Debrid token entry
 */
@OptIn(ExperimentalTvMaterial3Api::class)
@Composable
fun LoginScreen(
    onLoginSuccess: () -> Unit
) {
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var rdToken by remember { mutableStateOf("") }

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
                text = "Linkarr",
                style = MaterialTheme.typography.displayLarge
            )

            Text(
                text = "Direct streaming from Real-Debrid",
                style = MaterialTheme.typography.bodyLarge
            )

            Spacer(modifier = Modifier.height(32.dp))

            // Username field (placeholder - needs proper TextField implementation)
            Text(text = "Username: $username")

            // Password field (placeholder - needs proper TextField implementation)
            Text(text = "Password: ${if (password.isNotEmpty()) "****" else ""}")

            // RD Token field (placeholder - needs proper TextField implementation)
            Text(text = "RD Token: $rdToken")

            Spacer(modifier = Modifier.height(32.dp))

            Button(
                onClick = onLoginSuccess,
                modifier = Modifier.width(300.dp)
            ) {
                Text("Login")
            }
        }
    }
}
