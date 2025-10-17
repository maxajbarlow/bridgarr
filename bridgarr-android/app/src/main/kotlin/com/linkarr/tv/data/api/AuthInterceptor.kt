package com.linkarr.tv.data.api

import com.linkarr.tv.data.local.PreferencesManager
import kotlinx.coroutines.runBlocking
import okhttp3.Interceptor
import okhttp3.Response
import javax.inject.Inject

/**
 * Authentication Interceptor
 * Adds JWT token to API requests
 */
class AuthInterceptor @Inject constructor(
    private val preferencesManager: PreferencesManager
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()

        // Get token from preferences
        val token = runBlocking {
            preferencesManager.getAuthToken()
        }

        // If token exists, add Authorization header
        val newRequest = if (!token.isNullOrEmpty()) {
            request.newBuilder()
                .addHeader("Authorization", "Bearer $token")
                .build()
        } else {
            request
        }

        return chain.proceed(newRequest)
    }
}
