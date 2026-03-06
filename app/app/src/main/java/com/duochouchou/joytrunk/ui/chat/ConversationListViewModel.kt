package com.duochouchou.joytrunk.ui.chat

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.duochouchou.joytrunk.JoyTrunkApplication
import com.duochouchou.joytrunk.data.api.ConversationDto
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class ConversationListState(
    val list: List<ConversationDto> = emptyList(),
    val loading: Boolean = false,
    val error: String? = null,
)

class ConversationListViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application as JoyTrunkApplication
    private val _state = MutableStateFlow(ConversationListState())
    val state = _state.asStateFlow()

    fun load() {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, error = null)
            runCatching {
                val res = app.imApi.listConversations()
                if (!res.isSuccessful) throw Exception(res.errorBody()?.string()?.let { org.json.JSONObject(it).optString("error", "加载失败") } ?: "加载失败")
                res.body() ?: emptyList()
            }.onSuccess { _state.value = _state.value.copy(list = it, loading = false) }
                .onFailure { _state.value = _state.value.copy(loading = false, error = it.message) }
        }
    }
}
