package com.duochouchou.joytrunk.data.api

import com.google.gson.annotations.SerializedName

data class ConversationDto(
    val id: Int,
    val type: String?,
    val title: String?,
    @SerializedName("last_message") val lastMessage: LastMessageDto? = null,
    @SerializedName("updated_at") val updatedAt: String? = null,
    @SerializedName("unread_count") val unreadCount: Int = 0,
    @SerializedName("avatar_url") val avatarUrl: String? = null,
)

data class LastMessageDto(
    val content: String?,
    @SerializedName("created_at") val createdAt: String?,
)

data class MessageDto(
    val id: Int,
    @SerializedName("conversation_id") val conversationId: Int,
    @SerializedName("sender_id") val senderId: Int,
    val content: String?,
    @SerializedName("created_at") val createdAt: String?,
    @SerializedName("image_url") val imageUrl: String? = null,
)

data class CreateConversationRequest(
    val type: String,
    @SerializedName("peer_uid") val peerUid: String? = null,
    @SerializedName("employee_id") val employeeId: String? = null,
    val title: String? = null,
    @SerializedName("member_uids") val memberUids: List<String>? = null,
)

data class CreateConversationResponse(val id: Int)

data class GetMessagesResponse(
    val items: List<MessageDto>? = null,
    @SerializedName("has_more") val hasMore: Boolean? = null,
    @SerializedName("next_cursor") val nextCursor: String? = null,
)

data class SendMessageRequest(val content: String)
