package com.duochouchou.joytrunk.data.api

import com.google.gson.annotations.SerializedName

/** GET /api/users/me/usage 响应 */
data class UsageDto(
    val balance: Int? = null,
    val quota: Int? = null,
    @SerializedName("router_usage") val routerUsage: Any? = null,
    @SerializedName("custom_usage") val customUsage: Any? = null,
)
