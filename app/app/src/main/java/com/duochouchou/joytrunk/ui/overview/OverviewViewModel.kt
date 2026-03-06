package com.duochouchou.joytrunk.ui.overview

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.duochouchou.joytrunk.JoyTrunkApplication
import com.duochouchou.joytrunk.data.api.CliEmployeeDto
import com.duochouchou.joytrunk.data.api.UserDto
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class OverviewState(
    val user: UserDto? = null,
    val employees: List<CliEmployeeDto> = emptyList(),
    val loading: Boolean = false,
    val error: String? = null,
)

class OverviewViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application as JoyTrunkApplication
    private val _state = MutableStateFlow(OverviewState())
    val state = _state.asStateFlow()

    fun load() {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, error = null)
            runCatching {
                val me = app.userApi.getMe()
                if (!me.isSuccessful) throw Exception(me.errorBody()?.string()?.let { org.json.JSONObject(it).optString("error", "加载失败") } ?: "加载失败")
                me.body()!!
            }.onSuccess { user ->
                _state.value = _state.value.copy(user = user, loading = false)
            }.onFailure {
                _state.value = _state.value.copy(loading = false, error = it.message)
            }
            runCatching {
                val emp = app.cliApi.getEmployees()
                if (emp.isSuccessful) emp.body()?.employees ?: emptyList() else emptyList()
            }.onSuccess { list ->
                _state.value = _state.value.copy(employees = list)
            }
        }
    }
}
