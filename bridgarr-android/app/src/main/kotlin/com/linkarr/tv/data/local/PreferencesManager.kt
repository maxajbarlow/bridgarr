package com.linkarr.tv.data.local

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Preferences Manager
 * DataStore-based storage for user preferences and auth tokens
 */

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "linkarr_preferences")

@Singleton
class PreferencesManager @Inject constructor(
    @ApplicationContext private val context: Context
) {

    companion object {
        private val AUTH_TOKEN_KEY = stringPreferencesKey("auth_token")
        private val USERNAME_KEY = stringPreferencesKey("username")
        private val USER_ID_KEY = stringPreferencesKey("user_id")
        private val BASE_URL_KEY = stringPreferencesKey("base_url")
    }

    // Auth Token
    suspend fun saveAuthToken(token: String) {
        context.dataStore.edit { preferences ->
            preferences[AUTH_TOKEN_KEY] = token
        }
    }

    suspend fun getAuthToken(): String? {
        return context.dataStore.data.first()[AUTH_TOKEN_KEY]
    }

    val authTokenFlow: Flow<String?> = context.dataStore.data
        .map { preferences -> preferences[AUTH_TOKEN_KEY] }

    suspend fun clearAuthToken() {
        context.dataStore.edit { preferences ->
            preferences.remove(AUTH_TOKEN_KEY)
        }
    }

    // Username
    suspend fun saveUsername(username: String) {
        context.dataStore.edit { preferences ->
            preferences[USERNAME_KEY] = username
        }
    }

    suspend fun getUsername(): String? {
        return context.dataStore.data.first()[USERNAME_KEY]
    }

    val usernameFlow: Flow<String?> = context.dataStore.data
        .map { preferences -> preferences[USERNAME_KEY] }

    // User ID
    suspend fun saveUserId(userId: String) {
        context.dataStore.edit { preferences ->
            preferences[USER_ID_KEY] = userId
        }
    }

    suspend fun getUserId(): String? {
        return context.dataStore.data.first()[USER_ID_KEY]
    }

    // Base URL
    suspend fun saveBaseUrl(baseUrl: String) {
        context.dataStore.edit { preferences ->
            preferences[BASE_URL_KEY] = baseUrl
        }
    }

    suspend fun getBaseUrl(): String? {
        return context.dataStore.data.first()[BASE_URL_KEY]
    }

    val baseUrlFlow: Flow<String?> = context.dataStore.data
        .map { preferences -> preferences[BASE_URL_KEY] }

    // Clear all data (logout)
    suspend fun clearAll() {
        context.dataStore.edit { preferences ->
            preferences.clear()
        }
    }

    // Check if user is logged in
    suspend fun isLoggedIn(): Boolean {
        return getAuthToken() != null
    }

    val isLoggedInFlow: Flow<Boolean> = context.dataStore.data
        .map { preferences -> preferences[AUTH_TOKEN_KEY] != null }
}
