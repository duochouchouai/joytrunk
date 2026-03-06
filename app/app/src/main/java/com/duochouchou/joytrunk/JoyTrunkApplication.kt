package com.duochouchou.joytrunk

import android.app.Application
import com.duochouchou.joytrunk.data.api.AuthApi
import com.duochouchou.joytrunk.data.api.CliApi
import com.duochouchou.joytrunk.data.api.ImApi
import com.duochouchou.joytrunk.data.api.UserApi
import com.duochouchou.joytrunk.data.network.createAuthApi
import com.duochouchou.joytrunk.data.network.createCliApi
import com.duochouchou.joytrunk.data.network.createImApi
import com.duochouchou.joytrunk.data.network.createOkHttpClient
import com.duochouchou.joytrunk.data.network.createRetrofit
import com.duochouchou.joytrunk.data.network.createUserApi
import com.duochouchou.joytrunk.data.store.SettingsRepository
import com.duochouchou.joytrunk.data.ws.ImWebSocketManager
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking

class JoyTrunkApplication : Application() {

    val settingsRepository: SettingsRepository by lazy { SettingsRepository(this) }

    private fun getBaseUrl(): String = runBlocking { settingsRepository.baseUrl.first() }

    val okHttpClient by lazy { createOkHttpClient(settingsRepository) }

    val retrofit by lazy {
        createRetrofit(getBaseUrl(), okHttpClient)
    }

    val authApi: AuthApi by lazy { createAuthApi(retrofit) }
    val userApi: UserApi by lazy { createUserApi(retrofit) }
    val imApi: ImApi by lazy { createImApi(retrofit) }
    val cliApi: CliApi by lazy { createCliApi(retrofit) }

    val imWebSocketManager: ImWebSocketManager by lazy { ImWebSocketManager(settingsRepository) }

    override fun onCreate() {
        super.onCreate()
    }
}
