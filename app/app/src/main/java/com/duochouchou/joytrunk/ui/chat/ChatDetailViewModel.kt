package com.duochouchou.joytrunk.ui.chat

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.duochouchou.joytrunk.JoyTrunkApplication
import com.duochouchou.joytrunk.data.api.MessageDto
import com.duochouchou.joytrunk.data.ws.ImWebSocketManager
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.filter
import kotlinx.coroutines.launch

data class ChatDetailState(
    val messages: List<MessageDto> = emptyList(),
    val loading: Boolean = false,
    val sending: Boolean = false,
    val error: String? = null,
)

class ChatDetailViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application as JoyTrunkApplication
    private val _state = MutableStateFlow(ChatDetailState())
    val state = _state.asStateFlow()

    fun loadMessages(conversationId: Int) {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, error = null)
            runCatching {
                val res = app.imApi.getMessages(conversationId)
                if (!res.isSuccessful) throw Exception(res.errorBody()?.string()?.let { org.json.JSONObject(it).optString("error") } ?: "加载失败")
                res.body()?.items ?: emptyList()
            }.onSuccess { _state.value = _state.value.copy(messages = it, loading = false) }
                .onFailure { _state.value = _state.value.copy(loading = false, error = it.message) }
        }
    }

    fun sendMessage(conversationId: Int, content: String, onSent: () -> Unit) {
        if (content.isBlank()) return
        viewModelScope.launch {
            _state.value = _state.value.copy(sending = true, error = null)
            runCatching {
                val res = app.imApi.sendMessage(conversationId, com.duochouchou.joytrunk.data.api.SendMessageRequest(content))
                if (!res.isSuccessful) throw Exception(res.errorBody()?.string()?.let { org.json.JSONObject(it).optString("error") } ?: "发送失败")
                res.body()!!
            }.onSuccess { msg ->
                _state.value = _state.value.copy(
                    messages = _state.value.messages + msg,
                    sending = false,
                )
                onSent()
            }.onFailure { _state.value = _state.value.copy(sending = false, error = it.message) }
        }
    }

    fun subscribeReplies(conversationId: Int) {
        viewModelScope.launch {
            app.imWebSocketManager.incomingReply
                .filter { it.conversationId == conversationId }
                .collect { reply ->
                    val newMsg = MessageDto(
                        id = reply.messageId ?: -1,
                        conversationId = conversationId,
                        senderId = 0,
                        content = reply.content,
                        createdAt = null,
                    )
                    _state.value = _state.value.copy(messages = _state.value.messages + newMsg)
                }
        }
    }

    fun appendReply(content: String, conversationId: Int) {
        val newMsg = MessageDto(
            id = -1,
            conversationId = conversationId,
            senderId = 0,
            content = content,
            createdAt = null,
        )
        _state.value = _state.value.copy(messages = _state.value.messages + newMsg)
    }
}
