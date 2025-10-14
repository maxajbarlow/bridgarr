package com.linkarr.tv.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.linkarr.tv.ui.screens.detail.DetailScreen
import com.linkarr.tv.ui.screens.home.HomeScreen
import com.linkarr.tv.ui.screens.login.LoginScreen
import com.linkarr.tv.ui.screens.login.LoginViewModel

/**
 * Navigation Routes
 */
sealed class Screen(val route: String) {
    object Login : Screen("login")
    object Home : Screen("home")
    object Detail : Screen("detail/{mediaId}") {
        fun createRoute(mediaId: Int) = "detail/$mediaId"
    }
    object Player : Screen("player/{mediaId}?episodeId={episodeId}") {
        fun createRoute(mediaId: Int, episodeId: Int? = null): String {
            return if (episodeId != null) {
                "player/$mediaId?episodeId=$episodeId"
            } else {
                "player/$mediaId"
            }
        }
    }
}

/**
 * Main Navigation Graph
 */
@Composable
fun LinkarrNavigation(
    navController: NavHostController = rememberNavController(),
    isLoggedIn: Boolean
) {
    val startDestination = if (isLoggedIn) Screen.Home.route else Screen.Login.route

    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        // Login Screen
        composable(Screen.Login.route) {
            val viewModel: LoginViewModel = hiltViewModel()
            val uiState by viewModel.uiState.collectAsState()

            LoginScreen(
                uiState = uiState,
                onLogin = { username, password ->
                    viewModel.login(username, password)
                },
                onLoginSuccess = {
                    navController.navigate(Screen.Home.route) {
                        popUpTo(Screen.Login.route) { inclusive = true }
                    }
                }
            )
        }

        // Home Screen
        composable(Screen.Home.route) {
            HomeScreen(
                onMediaClick = { mediaId ->
                    navController.navigate(Screen.Detail.createRoute(mediaId))
                },
                onLogout = {
                    navController.navigate(Screen.Login.route) {
                        popUpTo(0) { inclusive = true }
                    }
                }
            )
        }

        // Detail Screen
        composable(
            route = Screen.Detail.route,
            arguments = listOf(
                navArgument("mediaId") { type = NavType.IntType }
            )
        ) {
            DetailScreen(
                onPlayClick = { mediaId, episodeId ->
                    navController.navigate(Screen.Player.createRoute(mediaId, episodeId))
                },
                onBackPress = {
                    navController.popBackStack()
                }
            )
        }

        // Player Screen (to be implemented)
        composable(
            route = Screen.Player.route,
            arguments = listOf(
                navArgument("mediaId") { type = NavType.IntType },
                navArgument("episodeId") {
                    type = NavType.IntType
                    nullable = true
                    defaultValue = null
                }
            )
        ) {
            // PlayerScreen will be implemented later
            // For now, just show a placeholder
        }
    }
}
