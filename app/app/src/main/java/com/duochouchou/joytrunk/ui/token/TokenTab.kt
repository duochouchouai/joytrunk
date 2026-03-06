package com.duochouchou.joytrunk.ui.token

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.widget.Toast
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ContentCopy
import androidx.compose.material.icons.filled.Key
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.duochouchou.joytrunk.JoyTrunkApplication
import com.duochouchou.joytrunk.ui.locale.AppStrings
import com.duochouchou.joytrunk.ui.locale.LocalAppLanguage
import com.duochouchou.joytrunk.ui.theme.JoyTrunkPrimary

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TokenTab() {
    val app = LocalContext.current.applicationContext as? JoyTrunkApplication
        ?: return
    val lang = LocalAppLanguage.current
    val viewModel: TokenViewModel = viewModel(
        factory = androidx.lifecycle.ViewModelProvider.AndroidViewModelFactory.getInstance(app),
    )
    val state by viewModel.state.collectAsState()
    LaunchedEffect(Unit) { viewModel.load() }

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text(AppStrings.get(lang, "token"), style = MaterialTheme.typography.titleLarge) },
                colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                    titleContentColor = MaterialTheme.colorScheme.onSurface,
                ),
            )
        },
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            state.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            if (state.loading && state.user == null) {
                Box(modifier = Modifier.fillMaxWidth().height(200.dp), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
                return@Scaffold
            }

            state.usage?.let { usage ->
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surface,
                        contentColor = MaterialTheme.colorScheme.onSurface,
                    ),
                    shape = RoundedCornerShape(16.dp),
                    elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                ) {
                    Column(Modifier.padding(20.dp)) {
                        Text(
                            AppStrings.get(lang, "token_usage"),
                            style = MaterialTheme.typography.titleMedium,
                        )
                        Spacer(Modifier.height(16.dp))
                        UsageBar(
                            used = ((usage.quota ?: 0) - (usage.balance ?: 0)).coerceAtLeast(0).toFloat(),
                            total = (usage.quota ?: 1).coerceAtLeast(1).toFloat(),
                        )
                        Spacer(Modifier.height(12.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                        ) {
                            Text(
                                "${AppStrings.get(lang, "balance")}: ${usage.balance ?: 0}",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.primary,
                            )
                            Text(
                                "${AppStrings.get(lang, "quota")}: ${usage.quota ?: 0}",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                }
            }

            state.user?.let { user ->
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surface,
                        contentColor = MaterialTheme.colorScheme.onSurface,
                    ),
                    shape = RoundedCornerShape(16.dp),
                    elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                ) {
                    Column(Modifier.padding(20.dp)) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Icon(
                                Icons.Default.Key,
                                contentDescription = null,
                                modifier = Modifier.size(20.dp),
                                tint = MaterialTheme.colorScheme.primary,
                            )
                            Spacer(Modifier.size(8.dp))
                            Text(AppStrings.get(lang, "api_key"), style = MaterialTheme.typography.titleMedium)
                        }
                        Spacer(Modifier.height(12.dp))
                        val displayKey = state.apiKeyRevealed ?: (user.apiKeyMasked ?: AppStrings.get(lang, "not_generated"))
                        val keyToCopy = state.apiKeyRevealed ?: user.apiKeyMasked
                        val context = LocalContext.current
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            if (keyToCopy != null) {
                                IconButton(
                                    onClick = {
                                        val cm = context.getSystemService(Context.CLIPBOARD_SERVICE) as? ClipboardManager
                                        cm?.setPrimaryClip(ClipData.newPlainText("API Key", keyToCopy))
                                        Toast.makeText(context, AppStrings.get(lang, "copied"), Toast.LENGTH_SHORT).show()
                                    },
                                    modifier = Modifier.size(32.dp),
                                ) {
                                    Icon(
                                        Icons.Default.ContentCopy,
                                        contentDescription = AppStrings.get(lang, "copy"),
                                        modifier = Modifier.size(18.dp),
                                    )
                                }
                                Spacer(Modifier.size(6.dp))
                            }
                            Text(
                                text = displayKey,
                                style = MaterialTheme.typography.bodyMedium,
                                modifier = Modifier.weight(1f),
                            )
                            if (state.apiKeyRevealed != null) {
                                Button(
                                    onClick = { viewModel.clearRevealedKey() },
                                    modifier = Modifier.padding(start = 4.dp),
                                ) {
                                    Text(AppStrings.get(lang, "hide"))
                                }
                            } else if (user.apiKeyMasked != null) {
                                Text(
                                    text = AppStrings.get(lang, "regen_hint"),
                                    style = MaterialTheme.typography.labelSmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                    modifier = Modifier.padding(start = 4.dp),
                                )
                            } else {
                                Button(onClick = { viewModel.generateApiKey() }) {
                                    Text(AppStrings.get(lang, "generate_api_key"))
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun UsageBar(
    used: Float,
    total: Float,
) {
    val usedRatio = (used / total).coerceIn(0f, 1f)
    val primary = JoyTrunkPrimary
    val trackColor = MaterialTheme.colorScheme.surfaceVariant

    Canvas(
        modifier = Modifier
            .fillMaxWidth()
            .height(12.dp),
    ) {
        val w = size.width
        val h = size.height
        val radius = h / 2f
        drawRoundRect(
            color = trackColor,
            topLeft = Offset(0f, 0f),
            size = Size(w, h),
            cornerRadius = CornerRadius(radius, radius),
        )
        if (usedRatio > 0f) {
            drawRoundRect(
                color = primary,
                topLeft = Offset(0f, 0f),
                size = Size(w * usedRatio, h),
                cornerRadius = CornerRadius(radius, radius),
            )
        }
    }
}
