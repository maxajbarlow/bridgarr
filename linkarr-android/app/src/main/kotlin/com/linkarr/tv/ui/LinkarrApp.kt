package com.linkarr.tv.ui

import androidx.compose.runtime.Composable
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.linkarr.tv.ui.screens.home.HomeScreen
import com.linkarr.tv.ui.screens.login.LoginScreen

/**
 * Main Linkarr App Composable
 * Handles top-level navigation
 */
@Composable
fun LinkarrApp() {
    val navController = rememberNavController()

    NavHost(
        navController = navController,
        startDestination = "login"
    ) {
        composable("login") {
            LoginScreen(
                onLoginSuccess = {
                    navController.navigate("home") {
                        popUpTo("login") { inclusive = true }
                    }
                }
            )
        }

        composable("home") {
            HomeScreen(navController = navController)
        }
    }
}
