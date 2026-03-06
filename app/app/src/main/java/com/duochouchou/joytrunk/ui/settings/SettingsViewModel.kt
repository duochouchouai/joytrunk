package com.duochouchou.joytrunk.ui.settings

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.duochouchou.joytrunk.JoyTrunkApplication
import com.duochouchou.joytrunk.data.store.SettingsRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

data class SettingsUiState(
    val name: String = "",
    val avatarUrl: String = "",
    val language: String = SettingsRepository.LANGUAGE_ZH,
    val darkTheme: Boolean = false,
    val loading: Boolean = false,
    val error: String? = null,
    val saveSuccess: Boolean = false,
    val passwordSuccess: Boolean = false,
)

class SettingsViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application as JoyTrunkApplication
    private val settings = app.settingsRepository
    private val _state = MutableStateFlow(SettingsUiState())

    val state = combine(
        _state,
        settings.userName,
        settings.userAvatarUrl,
        settings.language,
        settings.darkTheme,
    ) { s, name, avatar, lang, dark ->
        s.copy(
            name = name ?: "",
            avatarUrl = avatar ?: "",
            language = lang,
            darkTheme = dark,
        )
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), SettingsUiState())

    fun load() {
        viewModelScope.launch {
            runCatching {
                val me = app.userApi.getMe()
                if (!me.isSuccessful) return@runCatching
                me.body()?.let { u ->
                    settings.setUserCache(u.id.toString(), u.name, u.avatarUrl)
                }
            }
        }
    }

    fun updateName(name: String) { _state.value = _state.value.copy(name = name) }
    fun updateAvatarUrl(url: String) { _state.value = _state.value.copy(avatarUrl = url) }

    fun saveProfile() {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, error = null)
            runCatching {
                val res = app.userApi.updateMe(
                    mapOf(
                        "name" to _state.value.name,
                        "avatar_url" to _state.value.avatarUrl.takeIf { it.isNotBlank() },
                    )
                )
                if (!res.isSuccessful) throw Exception(res.errorBody()?.string()?.let { org.json.JSONObject(it).optString("error", "保存失败") } ?: "保存失败")
                res.body()?.let { settings.setUserCache(it.id.toString(), it.name, it.avatarUrl) }
            }.onSuccess { _state.value = _state.value.copy(loading = false, saveSuccess = true) }
                .onFailure { _state.value = _state.value.copy(loading = false, error = it.message) }
        }
    }

    fun setLanguage(lang: String) {
        viewModelScope.launch { settings.setLanguage(lang) }
    }

    fun setDarkTheme(dark: Boolean) {
        viewModelScope.launch { settings.setDarkTheme(dark) }
    }

    fun updatePassword(oldPassword: String, newPassword: String, onDone: (Boolean, String?) -> Unit) {
        viewModelScope.launch {
            runCatching {
                val res = app.userApi.updatePassword(
                    mapOf(
                        "old_password" to oldPassword,
                        "password" to newPassword,
                    )
                )
                if (!res.isSuccessful) throw Exception(res.errorBody()?.string()?.let { org.json.JSONObject(it).optString("error", "修改失败") } ?: "修改失败")
            }.onSuccess {
                _state.value = _state.value.copy(passwordSuccess = true)
                onDone(true, null)
            }
                .onFailure {
                    _state.value = _state.value.copy(error = it.message)
                    onDone(false, it.message)
                }
        }
    }

    fun clearPasswordSuccess() { _state.value = _state.value.copy(passwordSuccess = false) }

    fun logout() {
        viewModelScope.launch {
            settings.clearAuth()
            app.imWebSocketManager.disconnect()
        }
    }

    fun clearSaveSuccess() { _state.value = _state.value.copy(saveSuccess = false) }
    fun clearError() { _state.value = _state.value.copy(error = null) }
}
