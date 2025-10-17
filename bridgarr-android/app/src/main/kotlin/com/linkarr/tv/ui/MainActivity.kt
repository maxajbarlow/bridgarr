package com.linkarr.tv.ui

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import androidx.tv.material3.ExperimentalTvMaterial3Api
import androidx.tv.material3.Surface
import com.linkarr.tv.ui.theme.LinkarrTheme
import dagger.hilt.android.AndroidEntryPoint

/**
 * Main Activity for Linkarr TV
 * Handles navigation and displays the main UI
 */
@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    @OptIn(ExperimentalTvMaterial3Api::class)
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            LinkarrTheme {
                Surface(
                    modifier = Modifier.fillMaxSize()
                ) {
                    LinkarrApp()
                }
            }
        }
    }
}
