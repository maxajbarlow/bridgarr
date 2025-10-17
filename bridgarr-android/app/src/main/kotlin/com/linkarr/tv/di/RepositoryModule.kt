package com.linkarr.tv.di

import com.linkarr.tv.data.api.ApiService
import com.linkarr.tv.data.local.PreferencesManager
import com.linkarr.tv.data.repository.AuthRepository
import com.linkarr.tv.data.repository.MediaRepository
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

/**
 * Dependency Injection Module for Repositories
 */
@Module
@InstallIn(SingletonComponent::class)
object RepositoryModule {

    @Provides
    @Singleton
    fun provideAuthRepository(
        apiService: ApiService,
        preferencesManager: PreferencesManager
    ): AuthRepository {
        return AuthRepository(apiService, preferencesManager)
    }

    @Provides
    @Singleton
    fun provideMediaRepository(
        apiService: ApiService
    ): MediaRepository {
        return MediaRepository(apiService)
    }
}
