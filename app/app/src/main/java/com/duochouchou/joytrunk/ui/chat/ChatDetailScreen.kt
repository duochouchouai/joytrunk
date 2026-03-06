package com.duochouchou.joytrunk.ui.chat

import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.SmartToy
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilledTonalIconButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import coil.compose.AsyncImage
import com.duochouchou.joytrunk.JoyTrunkApplication
import com.duochouchou.joytrunk.data.api.MessageDto
import com.duochouchou.joytrunk.ui.locale.AppStrings
import com.duochouchou.joytrunk.ui.locale.LocalAppLanguage
import com.duochouchou.joytrunk.ui.theme.ChatBubbleGrayDark
import com.duochouchou.joytrunk.ui.theme.ChatBubbleGrayLight

private val THINK_REGEX = Regex("""<think>([\s\S]*?)</think>""", RegexOption.IGNORE_CASE)

private data class ParsedContent(val visible: String, val thinkBlocks: List<String>)

private fun parseContent(content: String?): ParsedContent {
    if (content.isNullOrBlank()) return ParsedContent("", emptyList())
    val blocks = mutableListOf<String>()
    val visible = THINK_REGEX.replace(content) { match ->
        blocks.add(match.groupValues[1].trim())
        ""
    }.trim()
    return ParsedContent(visible, blocks)
}

@OptIn(ExperimentalFoundationApi::class, ExperimentalMaterial3Api::class)
@Composable
fun ChatDetailScreen(
    conversationId: Int,
    onBack: () -> Unit,
) {
    val app = LocalContext.current.applicationContext as? JoyTrunkApplication ?: return
    val viewModel: ChatDetailViewModel = viewModel(
        factory = androidx.lifecycle.ViewModelProvider.AndroidViewModelFactory.getInstance(app),
    )
    val state by viewModel.state.collectAsState()
    val userAvatarUrl by app.settingsRepository.userAvatarUrl.collectAsState(initial = null)
    val userId by app.settingsRepository.userId.collectAsState(initial = null)
    val lang = LocalAppLanguage.current
    var inputText by remember { mutableStateOf("") }
    val listState = rememberLazyListState()

    LaunchedEffect(conversationId) {
        viewModel.loadMessages(conversationId)
        viewModel.subscribeReplies(conversationId)
    }
    LaunchedEffect(state.messages.size) {
        if (state.messages.isNotEmpty()) listState.animateScrollToItem(state.messages.size - 1)
    }

    Column(Modifier.fillMaxSize()) {
        CenterAlignedTopAppBar(
            title = {
                Text(
                    AppStrings.get(lang, "session"),
                    style = MaterialTheme.typography.titleLarge,
                )
            },
            navigationIcon = {
                IconButton(onClick = onBack) {
                    Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = AppStrings.get(lang, "back"))
                }
            },
            colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
                containerColor = MaterialTheme.colorScheme.surface,
                titleContentColor = MaterialTheme.colorScheme.onSurface,
            ),
        )
        state.error?.let { Text(it, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(8.dp)) }
        LazyColumn(
            modifier = Modifier.weight(1f).fillMaxWidth(),
            state = listState,
            contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 12.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            items(state.messages) { msg ->
                val myId = remember(userId) { userId?.toIntOrNull() }
                MessageBubble(
                    message = msg,
                    isMe = (myId != null && msg.senderId == myId) || (myId == null && msg.senderId != 0),
                    userAvatarUrl = userAvatarUrl,
                )
            }
        }
        HorizontalDivider()
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            OutlinedTextField(
                value = inputText,
                onValueChange = { inputText = it },
                modifier = Modifier.weight(1f),
                placeholder = { Text(AppStrings.get(lang, "input_message")) },
                minLines = 1,
                maxLines = 4,
            )
            Spacer(Modifier.size(8.dp))
            FilledTonalIconButton(
                onClick = {
                    viewModel.sendMessage(conversationId, inputText) { inputText = "" }
                },
                enabled = inputText.isNotBlank() && !state.sending,
            ) {
                Icon(Icons.Default.Send, contentDescription = AppStrings.get(lang, "send"))
            }
        }
    }
}

@Composable
private fun MessageBubble(
    message: MessageDto,
    isMe: Boolean,
    userAvatarUrl: String?,
) {
    val parsed = remember(message.content) { parseContent(message.content) }
    if (isMe) {
        UserMessageBubble(parsed = parsed, userAvatarUrl = userAvatarUrl)
    } else {
        AiMessageBubble(parsed = parsed, messageId = message.id)
    }
}

@Composable
private fun UserMessageBubble(
    parsed: ParsedContent,
    userAvatarUrl: String?,
) {
    val bubbleColor = MaterialTheme.colorScheme.primary
    val onBubbleColor = MaterialTheme.colorScheme.onPrimary
    val avatarSize = 40.dp
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.End,
        verticalAlignment = Alignment.Bottom,
    ) {
        Spacer(Modifier.weight(1f))
        Card(
            modifier = Modifier.widthIn(max = 280.dp),
            colors = CardDefaults.cardColors(containerColor = bubbleColor, contentColor = onBubbleColor),
            shape = RoundedCornerShape(16.dp, 16.dp, 4.dp, 16.dp),
            elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
        ) {
            Column(Modifier.padding(12.dp)) {
                if (parsed.visible.isNotBlank()) {
                    Text(
                        text = parsed.visible,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }
        }
        Spacer(Modifier.size(8.dp))
        Box(
            modifier = Modifier
                .size(avatarSize)
                .clip(CircleShape)
                .background(MaterialTheme.colorScheme.primary),
            contentAlignment = Alignment.Center,
        ) {
            if (!userAvatarUrl.isNullOrBlank()) {
                AsyncImage(
                    model = userAvatarUrl,
                    contentDescription = null,
                    modifier = Modifier.fillMaxSize().clip(CircleShape),
                    contentScale = ContentScale.Crop,
                )
            } else {
                Icon(
                    Icons.Default.Person,
                    contentDescription = null,
                    modifier = Modifier.size(24.dp),
                    tint = MaterialTheme.colorScheme.onPrimary,
                )
            }
        }
    }
}

@Composable
private fun AiMessageBubble(
    parsed: ParsedContent,
    messageId: Int,
) {
    var thinkExpanded by remember(messageId) { mutableStateOf(false) }
    val isDark = isSystemInDarkTheme()
    val lang = LocalAppLanguage.current
    val bubbleColor = if (isDark) ChatBubbleGrayDark else ChatBubbleGrayLight
    val onBubbleColor = MaterialTheme.colorScheme.onSurface
    val avatarSize = 40.dp
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.Start,
        verticalAlignment = Alignment.Bottom,
    ) {
        Box(
            modifier = Modifier
                .size(avatarSize)
                .clip(CircleShape)
                .background(bubbleColor),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                Icons.Default.SmartToy,
                contentDescription = null,
                modifier = Modifier.size(24.dp),
                tint = onBubbleColor,
            )
        }
        Spacer(Modifier.size(8.dp))
        Card(
            modifier = Modifier.widthIn(max = 280.dp),
            colors = CardDefaults.cardColors(containerColor = bubbleColor, contentColor = onBubbleColor),
            shape = RoundedCornerShape(16.dp, 16.dp, 16.dp, 4.dp),
            border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
        ) {
            Column(Modifier.padding(12.dp)) {
                if (parsed.thinkBlocks.isNotEmpty()) {
                    Row(
                        modifier = Modifier
                            .clickable { thinkExpanded = !thinkExpanded }
                            .padding(vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(
                            text = if (thinkExpanded) "▼ " else "▶ ",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        Text(
                            text = if (thinkExpanded) AppStrings.get(lang, "think_collapse") else AppStrings.get(lang, "think_expand"),
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                    if (thinkExpanded) {
                        Column(
                            modifier = Modifier
                                .padding(top = 4.dp)
                                .heightIn(max = 200.dp)
                                .verticalScroll(rememberScrollState())
                                .background(bubbleColor.copy(alpha = 0.5f), RoundedCornerShape(8.dp))
                                .padding(8.dp),
                        ) {
                            parsed.thinkBlocks.forEach { block ->
                                Text(
                                    text = block,
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                    modifier = Modifier.padding(vertical = 2.dp),
                                )
                            }
                        }
                    }
                }
                if (parsed.visible.isNotBlank()) {
                    if (parsed.thinkBlocks.isNotEmpty()) Spacer(Modifier.size(6.dp))
                    Text(
                        text = parsed.visible,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }
        }
        Spacer(Modifier.weight(1f))
    }
}
