package com.duochouchou.joytrunk.data.dto

import com.google.gson.annotations.SerializedName

/** 登录/注册响应 */
data class AuthResponse(
    @SerializedName("token") val token: String,
    @SerializedName("user") val user: UserDto?
)

data class UserDto(
    @SerializedName("id") val id: Int,
    @SerializedName("name") val name: String?,
    @SerializedName("avatar_url") val avatarUrl: String?,
    @SerializedName("balance") val balance: Int?,
    @SerializedName("api_key_masked") val apiKeyMasked: String?,
    @SerializedName("phone") val phone: String?,
    @SerializedName("email") val email: String?,
    @SerializedName("uid") val uid: String?,
    @SerializedName("sync_joytrunk_chat") val syncJoytrunkChat: Boolean?
)
