package com.duochouchou.joytrunk.data.api

import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface AuthApi {
    @POST("api/auth/send-code")
    suspend fun sendCode(@Body body: SendCodeRequest): Response<SendCodeResponse>

    @POST("api/auth/login-by-code")
    suspend fun loginByCode(@Body body: LoginByCodeRequest): Response<AuthResponse>

    @POST("api/auth/send-email-code")
    suspend fun sendEmailCode(@Body body: SendEmailCodeRequest): Response<SendCodeResponse>

    @POST("api/auth/login-by-email-code")
    suspend fun loginByEmailCode(@Body body: LoginByEmailCodeRequest): Response<AuthResponse>

    @POST("api/auth/login-by-password")
    suspend fun loginByPassword(@Body body: LoginByPasswordRequest): Response<AuthResponse>
}

interface UserApi {
    @GET("api/users/me")
    suspend fun getMe(): Response<UserDto>

    @PATCH("api/users/me")
    suspend fun updateMe(@Body body: Map<String, Any?>): Response<UserDto>

    @POST("api/users/me/api-key")
    suspend fun generateApiKey(): Response<GenerateApiKeyResponse>

    @GET("api/users/me/usage")
    suspend fun getUsage(): Response<UsageDto>

    @PATCH("api/users/me/password")
    suspend fun updatePassword(@Body body: Map<String, String>): Response<Unit>
}

data class GenerateApiKeyResponse(val api_key: String?)

interface ImApi {
    @GET("api/im/conversations")
    suspend fun listConversations(): Response<List<ConversationDto>>

    @POST("api/im/conversations")
    suspend fun createConversation(@Body body: CreateConversationRequest): Response<CreateConversationResponse>

    @GET("api/im/conversations/{id}/messages")
    suspend fun getMessages(
        @Path("id") conversationId: Int,
        @Query("limit") limit: Int? = 50,
        @Query("before") before: Int? = null,
        @Query("after") after: Int? = null,
    ): Response<GetMessagesResponse>

    @POST("api/im/conversations/{id}/messages")
    suspend fun sendMessage(@Path("id") conversationId: Int, @Body body: SendMessageRequest): Response<MessageDto>
}

interface CliApi {
    @GET("api/cli/employees")
    suspend fun getEmployees(): Response<CliEmployeesResponse>
}
