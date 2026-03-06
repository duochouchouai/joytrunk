package com.duochouchou.joytrunk.ui.token

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.duochouchou.joytrunk.JoyTrunkApplication
import com.duochouchou.joytrunk.data.api.UsageDto
import com.duochouchou.joytrunk.data.api.UserDto
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class TokenState(
    val user: UserDto? = null,
    val usage: UsageDto? = null,
    val apiKeyRevealed: String? = null,
    val loading: Boolean = false,
    val error: String? = null,
)

class TokenViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application as JoyTrunkApplication
    private val _state = MutableStateFlow(TokenState())
    val state = _state.asStateFlow()

    fun load() {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, error = null)
            runCatching {
                val me = app.userApi.getMe()
                if (!me.isSuccessful) throw Exception(me.errorBody()?.string()?.let { org.json.JSONObject(it).optString("error") } ?: "加载失败")
                me.body()!!
            }.onSuccess { user ->
                _state.value = _state.value.copy(user = user, loading = false)
            }.onFailure {
                _state.value = _state.value.copy(loading = false, error = it.message)
            }
            runCatching {
                val u = app.userApi.getUsage()
                if (u.isSuccessful) u.body() else null
            }.onSuccess { usage ->
                _state.value = _state.value.copy(usage = usage)
            }
        }
    }

    fun generateApiKey() {
        viewModelScope.launch {
            runCatching {
                val res = app.userApi.generateApiKey()
                if (!res.isSuccessful) throw Exception(res.errorBody()?.string()?.let { org.json.JSONObject(it).optString("error") } ?: "生成失败")
                res.body()?.api_key
            }.onSuccess { key ->
                _state.value = _state.value.copy(apiKeyRevealed = key)
                load()
            }.onFailure {
                _state.value = _state.value.copy(error = it.message)
            }
        }
    }

    fun clearRevealedKey() {
        _state.value = _state.value.copy(apiKeyRevealed = null)
    }
}
