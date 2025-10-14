package com.linkarr.tv.data.repository

import com.linkarr.tv.data.api.ApiService
import com.linkarr.tv.data.local.PreferencesManager
import com.linkarr.tv.data.model.*
import com.linkarr.tv.util.Result
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Authentication Repository
 * Handles authentication operations and user management
 */
@Singleton
class AuthRepository @Inject constructor(
    private val apiService: ApiService,
    private val preferencesManager: PreferencesManager
) {

    val isLoggedInFlow: Flow<Boolean> = preferencesManager.isLoggedInFlow
    val usernameFlow: Flow<String?> = preferencesManager.usernameFlow

    suspend fun login(username: String, password: String): Result<UserResponse> {
        return try {
            val response = apiService.login(username, password)

            if (response.isSuccessful && response.body() != null) {
                val tokenResponse = response.body()!!

                // Save auth token
                preferencesManager.saveAuthToken(tokenResponse.accessToken)
                preferencesManager.saveUsername(username)

                // Fetch user details
                val userResponse = apiService.getCurrentUser()
                if (userResponse.isSuccessful && userResponse.body() != null) {
                    val user = userResponse.body()!!
                    preferencesManager.saveUserId(user.id.toString())
                    Result.Success(user)
                } else {
                    Result.Error("Failed to fetch user details")
                }
            } else {
                Result.Error(response.message() ?: "Login failed")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error occurred")
        }
    }

    suspend fun register(
        username: String,
        email: String,
        password: String
    ): Result<UserResponse> {
        return try {
            val request = RegisterRequest(username, email, password)
            val response = apiService.register(request)

            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.message() ?: "Registration failed")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error occurred")
        }
    }

    suspend fun getCurrentUser(): Result<UserResponse> {
        return try {
            val response = apiService.getCurrentUser()

            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.message() ?: "Failed to fetch user")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error occurred")
        }
    }

    suspend fun storeRdToken(rdToken: String): Result<UserResponse> {
        return try {
            val request = RdTokenRequest(rdToken)
            val response = apiService.storeRdToken(request)

            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.message() ?: "Failed to store RD token")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error occurred")
        }
    }

    suspend fun removeRdToken(): Result<Unit> {
        return try {
            val response = apiService.removeRdToken()

            if (response.isSuccessful) {
                Result.Success(Unit)
            } else {
                Result.Error(response.message() ?: "Failed to remove RD token")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error occurred")
        }
    }

    suspend fun logout() {
        preferencesManager.clearAll()
    }

    suspend fun isLoggedIn(): Boolean {
        return preferencesManager.isLoggedIn()
    }
}
