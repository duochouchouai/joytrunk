package com.duochouchou.joytrunk.data.api

import com.google.gson.annotations.SerializedName

/** 登录/注册响应 */
data class AuthResponse(
    val token: String,
    val user: UserDto?
)

data class UserDto(
    val id: Int,
    val name: String?,
    @SerializedName("avatar_url") val avatarUrl: String? = null,
    val balance: Int? = null,
    @SerializedName("api_key_masked") val apiKeyMasked: String? = null,
    val phone: String? = null,
    val email: String? = null,
    val uid: String? = null,
    @SerializedName("sync_joytrunk_chat") val syncJoytrunkChat: Boolean? = null,
)

data class SendCodeRequest(val phone: String)
data class LoginByCodeRequest(val phone: String, val code: String)
data class SendEmailCodeRequest(val email: String)
data class LoginByEmailCodeRequest(val email: String, val code: String)
data class LoginByPasswordRequest(val account: String, val password: String)

data class SendCodeResponse(val ok: Boolean? = null, val message: String? = null, val sent: Boolean? = null)
