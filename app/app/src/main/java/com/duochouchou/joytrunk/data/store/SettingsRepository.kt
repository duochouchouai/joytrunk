package com.duochouchou.joytrunk.data.store

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.runBlocking

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "joytrunk_prefs")

class SettingsRepository(private val context: Context) {

    /** 供 OkHttp Interceptor 同步读取 token */
    @Volatile
    var tokenSync: String? = null
        private set

    init {
        runBlocking { refreshTokenSync() }
    }

    private object Keys {
        val TOKEN = stringPreferencesKey("token")
        val OWNER_ID = stringPreferencesKey("owner_id")
        val BASE_URL = stringPreferencesKey("base_url")
        val USER_NAME = stringPreferencesKey("user_name")
        val USER_AVATAR_URL = stringPreferencesKey("user_avatar_url")
        val USER_ID = stringPreferencesKey("user_id")
        val LANGUAGE = stringPreferencesKey("language")
        val DARK_THEME = booleanPreferencesKey("dark_theme")
    }

    val token: Flow<String?> = context.dataStore.data.map { prefs ->
        prefs[Keys.TOKEN] ?: prefs[Keys.OWNER_ID]
    }

    suspend fun getTokenSync(): String? {
        var out: String? = null
        context.dataStore.data.map { prefs ->
            out = prefs[Keys.TOKEN] ?: prefs[Keys.OWNER_ID]
        }
        return out
    }

    suspend fun setAuth(tokenOrOwnerId: String?, isNumericId: Boolean = false) {
        context.dataStore.edit { prefs ->
            if (tokenOrOwnerId == null) {
                prefs.remove(Keys.TOKEN)
                prefs.remove(Keys.OWNER_ID)
            } else {
                if (isNumericId) {
                    prefs[Keys.OWNER_ID] = tokenOrOwnerId
                    prefs.remove(Keys.TOKEN)
                } else {
                    prefs[Keys.TOKEN] = tokenOrOwnerId
                    prefs.remove(Keys.OWNER_ID)
                }
            }
        }
        tokenSync = tokenOrOwnerId
    }

    suspend fun refreshTokenSync() {
        tokenSync = context.dataStore.data.map { it[Keys.TOKEN] ?: it[Keys.OWNER_ID] }.first()
    }

    val baseUrl: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[Keys.BASE_URL] ?: DEFAULT_BASE_URL
    }

    suspend fun setBaseUrl(url: String) {
        context.dataStore.edit { it[Keys.BASE_URL] = url }
    }

    suspend fun setUserCache(id: String?, name: String?, avatarUrl: String?) {
        context.dataStore.edit {
            if (id != null) it[Keys.USER_ID] = id else it.remove(Keys.USER_ID)
            if (name != null) it[Keys.USER_NAME] = name else it.remove(Keys.USER_NAME)
            if (avatarUrl != null) it[Keys.USER_AVATAR_URL] = avatarUrl else it.remove(Keys.USER_AVATAR_URL)
        }
    }

    val userName: Flow<String?> = context.dataStore.data.map { it[Keys.USER_NAME] }
    val userAvatarUrl: Flow<String?> = context.dataStore.data.map { it[Keys.USER_AVATAR_URL] }
    val userId: Flow<String?> = context.dataStore.data.map { it[Keys.USER_ID] }

    val language: Flow<String> = context.dataStore.data.map { it[Keys.LANGUAGE] ?: LANGUAGE_ZH }
    suspend fun setLanguage(lang: String) {
        context.dataStore.edit { it[Keys.LANGUAGE] = lang }
    }

    val darkTheme: Flow<Boolean> = context.dataStore.data.map { it[Keys.DARK_THEME] ?: false }
    suspend fun setDarkTheme(dark: Boolean) {
        context.dataStore.edit { it[Keys.DARK_THEME] = dark }
    }

    suspend fun clearAuth() {
        context.dataStore.edit {
            it.remove(Keys.TOKEN)
            it.remove(Keys.OWNER_ID)
            it.remove(Keys.USER_ID)
            it.remove(Keys.USER_NAME)
            it.remove(Keys.USER_AVATAR_URL)
        }
        tokenSync = null
    }

    companion object {
        const val DEFAULT_BASE_URL = "http://10.0.2.2:32891"
        const val LANGUAGE_ZH = "zh"
        const val LANGUAGE_EN = "en"
    }
}
