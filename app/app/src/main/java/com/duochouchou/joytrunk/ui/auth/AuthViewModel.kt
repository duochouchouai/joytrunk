package com.duochouchou.joytrunk.ui.auth

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.duochouchou.joytrunk.JoyTrunkApplication
import com.duochouchou.joytrunk.data.api.AuthResponse
import com.duochouchou.joytrunk.data.api.LoginByCodeRequest
import com.duochouchou.joytrunk.data.api.LoginByEmailCodeRequest
import com.duochouchou.joytrunk.data.api.LoginByPasswordRequest
import com.duochouchou.joytrunk.data.api.SendCodeRequest
import com.duochouchou.joytrunk.data.api.SendEmailCodeRequest
import com.duochouchou.joytrunk.data.store.SettingsRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

data class AuthUiState(
    val loading: Boolean = false,
    val error: String? = null,
    val loginSuccess: Boolean = false,
)

class AuthViewModel(application: Application) : AndroidViewModel(application) {

    private val app = application as JoyTrunkApplication
    private val authApi = app.authApi
    private val settings: SettingsRepository = app.settingsRepository

    private val _uiState = MutableStateFlow(AuthUiState())
    val uiState = _uiState.asStateFlow()

    fun sendPhoneCode(phone: String) = viewModelScope.launch {
        _uiState.value = _uiState.value.copy(loading = true, error = null)
        runCatching {
            val res = authApi.sendCode(SendCodeRequest(phone))
            if (!res.isSuccessful) {
                val body = res.errorBody()?.string()
                throw Exception(body?.let { org.json.JSONObject(it).optString("error", "发送失败") } ?: "发送失败")
            }
        }.onFailure { _uiState.value = _uiState.value.copy(loading = false, error = it.message) }
            .onSuccess { _uiState.value = _uiState.value.copy(loading = false) }
    }

    fun loginByPhoneCode(phone: String, code: String) = viewModelScope.launch {
        _uiState.value = _uiState.value.copy(loading = true, error = null)
        runCatching {
            val res = authApi.loginByCode(LoginByCodeRequest(phone, code))
            if (!res.isSuccessful) {
                val body = res.errorBody()?.string()
                throw Exception(body?.let { org.json.JSONObject(it).optString("error", "登录失败") } ?: "登录失败")
            }
            res.body()!!
        }.onFailure { _uiState.value = _uiState.value.copy(loading = false, error = it.message) }
            .onSuccess { onAuthSuccess(it) }
    }

    fun sendEmailCode(email: String) = viewModelScope.launch {
        _uiState.value = _uiState.value.copy(loading = true, error = null)
        runCatching {
            val res = authApi.sendEmailCode(SendEmailCodeRequest(email))
            if (!res.isSuccessful) {
                val body = res.errorBody()?.string()
                throw Exception(body?.let { org.json.JSONObject(it).optString("error", "发送失败") } ?: "发送失败")
            }
        }.onFailure { _uiState.value = _uiState.value.copy(loading = false, error = it.message) }
            .onSuccess { _uiState.value = _uiState.value.copy(loading = false) }
    }

    fun loginByEmailCode(email: String, code: String) = viewModelScope.launch {
        _uiState.value = _uiState.value.copy(loading = true, error = null)
        runCatching {
            val res = authApi.loginByEmailCode(LoginByEmailCodeRequest(email, code))
            if (!res.isSuccessful) {
                val body = res.errorBody()?.string()
                throw Exception(body?.let { org.json.JSONObject(it).optString("error", "登录失败") } ?: "登录失败")
            }
            res.body()!!
        }.onFailure { _uiState.value = _uiState.value.copy(loading = false, error = it.message) }
            .onSuccess { onAuthSuccess(it) }
    }

    fun loginByPassword(account: String, password: String) = viewModelScope.launch {
        _uiState.value = _uiState.value.copy(loading = true, error = null)
        runCatching {
            val res = authApi.loginByPassword(LoginByPasswordRequest(account, password))
            if (!res.isSuccessful) {
                val body = res.errorBody()?.string()
                throw Exception(body?.let { org.json.JSONObject(it).optString("error", "登录失败") } ?: "登录失败")
            }
            res.body()!!
        }.onFailure { _uiState.value = _uiState.value.copy(loading = false, error = it.message) }
            .onSuccess { onAuthSuccess(it) }
    }

    private suspend fun onAuthSuccess(response: AuthResponse) {
        val token = response.token
        val isNumericId = token.length < 50 && token.all { it.isDigit() }
        settings.setAuth(token, isNumericId)
        response.user?.let { u ->
            settings.setUserCache(u.id.toString(), u.name, u.avatarUrl)
        }
        _uiState.value = _uiState.value.copy(loading = false, error = null, loginSuccess = true)
    }

    fun clearError() { _uiState.value = _uiState.value.copy(error = null) }
}
