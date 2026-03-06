package com.duochouchou.joytrunk.ui.chat

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.duochouchou.joytrunk.JoyTrunkApplication
import com.duochouchou.joytrunk.data.api.CliEmployeeDto
import com.duochouchou.joytrunk.data.api.CreateConversationRequest
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class CreateConversationState(
    val employees: List<CliEmployeeDto> = emptyList(),
    val selectedEmployeeId: String? = null,
    val loading: Boolean = false,
    val creating: Boolean = false,
    val error: String? = null,
)

class CreateConversationViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application as JoyTrunkApplication
    private val _state = MutableStateFlow(CreateConversationState())
    val state = _state.asStateFlow()

    fun loadEmployees() {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, error = null)
            runCatching {
                val res = app.cliApi.getEmployees()
                if (!res.isSuccessful) throw Exception(res.errorBody()?.string()?.let { org.json.JSONObject(it).optString("error") } ?: "加载失败")
                res.body()?.employees ?: emptyList()
            }.onSuccess { _state.value = _state.value.copy(employees = it, loading = false) }
                .onFailure { _state.value = _state.value.copy(loading = false, error = it.message) }
        }
    }

    fun selectEmployee(id: String?) { _state.value = _state.value.copy(selectedEmployeeId = id) }

    fun createConversation(onCreated: (Int) -> Unit) {
        val empId = _state.value.selectedEmployeeId?.trim() ?: run {
            _state.value = _state.value.copy(error = "请选择一名员工")
            return
        }
        viewModelScope.launch {
            _state.value = _state.value.copy(creating = true, error = null)
            runCatching {
                val res = app.imApi.createConversation(
                    CreateConversationRequest(
                        type = "direct",
                        peerUid = "joytrunk",
                        employeeId = empId,
                    )
                )
                if (!res.isSuccessful) throw Exception(res.errorBody()?.string()?.let { org.json.JSONObject(it).optString("error") } ?: "创建失败")
                res.body()!!.id
            }.onSuccess {
                _state.value = _state.value.copy(creating = false)
                onCreated(it)
            }
                .onFailure { _state.value = _state.value.copy(creating = false, error = it.message) }
        }
    }
}
