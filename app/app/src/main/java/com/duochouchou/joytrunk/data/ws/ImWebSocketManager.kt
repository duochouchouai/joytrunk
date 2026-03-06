package com.duochouchou.joytrunk.data.ws

import com.duochouchou.joytrunk.data.store.SettingsRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/** WebSocket /ws/im 连接管理：鉴权、收包、重连，向 UI 暴露连接状态与 joytrunk_reply 消息 */
class ImWebSocketManager(private val settingsRepository: SettingsRepository) {

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(0, TimeUnit.SECONDS)
        .writeTimeout(15, TimeUnit.SECONDS)
        .pingInterval(30, TimeUnit.SECONDS)
        .build()

    private var webSocket: WebSocket? = null

    private val _connectionState = MutableSharedFlow<ConnectionState>(replay = 1)
    val connectionState: SharedFlow<ConnectionState> = _connectionState.asSharedFlow()

    private val _incomingReply = MutableSharedFlow<JoytrunkReply>(extraBufferCapacity = 64)
    val incomingReply: SharedFlow<JoytrunkReply> = _incomingReply.asSharedFlow()

    sealed class ConnectionState {
        object Disconnected : ConnectionState()
        object Connecting : ConnectionState()
        object Connected : ConnectionState()
        data class Error(val message: String) : ConnectionState()
    }

    data class JoytrunkReply(
        val conversationId: Int,
        val content: String,
        val messageId: Int? = null,
    )

    init {
        scope.launch { _connectionState.emit(ConnectionState.Disconnected) }
    }

    fun connect(baseUrl: String) {
        val token = settingsRepository.tokenSync
        if (token.isNullOrEmpty()) {
            scope.launch { _connectionState.emit(ConnectionState.Disconnected) }
            return
        }
        val wsUrl = baseUrl
            .replace("http://", "ws://")
            .replace("https://", "wss://")
            .trimEnd('/') + "/ws/im"
        scope.launch { _connectionState.emit(ConnectionState.Connecting) }
        val request = Request.Builder().url(wsUrl).build()
        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                val auth = JSONObject().apply {
                    put("type", "auth")
                    put("token", token)
                }
                webSocket.send(auth.toString())
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val json = JSONObject(text)
                    when (json.optString("type")) {
                        "auth_ok" -> scope.launch { _connectionState.emit(ConnectionState.Connected) }
                        "joytrunk_reply" -> {
                            val convId = json.optInt("conversation_id", 0)
                            val content = json.optString("content", "")
                            val msgId = if (json.has("message_id")) json.optInt("message_id", 0) else null
                            if (convId != 0) {
                                scope.launch {
                                    _incomingReply.emit(JoytrunkReply(convId, content, msgId?.takeIf { it > 0 }))
                                }
                            }
                        }
                    }
                } catch (_: Exception) {}
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {}
            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                scope.launch { _connectionState.emit(ConnectionState.Disconnected) }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                scope.launch { _connectionState.emit(ConnectionState.Error(t.message ?: "Unknown")) }
            }
        })
    }

    fun disconnect() {
        webSocket?.close(1000, null)
        webSocket = null
        scope.launch { _connectionState.emit(ConnectionState.Disconnected) }
    }
}
