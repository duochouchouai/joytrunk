package com.duochouchou.joytrunk.data.api

data class CliEmployeesResponse(val employees: List<CliEmployeeDto> = emptyList())

data class CliEmployeeDto(
    val id: String,
    val name: String? = null,
)
