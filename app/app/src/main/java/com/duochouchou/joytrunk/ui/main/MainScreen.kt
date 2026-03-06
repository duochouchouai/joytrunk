package com.duochouchou.joytrunk.ui.main

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Chat
import androidx.compose.material.icons.filled.Key
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.navigation.compose.rememberNavController
import com.duochouchou.joytrunk.JoyTrunkApplication
import kotlinx.coroutines.flow.first
import com.duochouchou.joytrunk.ui.chat.ChatTab
import com.duochouchou.joytrunk.ui.locale.AppStrings
import com.duochouchou.joytrunk.ui.locale.LocalAppLanguage
import com.duochouchou.joytrunk.ui.overview.OverviewTab
import com.duochouchou.joytrunk.ui.settings.SettingsTab
import com.duochouchou.joytrunk.ui.token.TokenTab

@Composable
fun MainScreen(
    onLogout: () -> Unit = {},
    navController: androidx.navigation.NavHostController = rememberNavController(),
) {
    val app = LocalContext.current.applicationContext as? JoyTrunkApplication
    val lang = LocalAppLanguage.current
    LaunchedEffect(Unit) {
        app?.let {
            val baseUrl = it.settingsRepository.baseUrl.first()
            it.imWebSocketManager.connect(baseUrl)
        }
    }
    var selectedTab by remember { mutableIntStateOf(0) }
    var chatTabAtRoot by remember { mutableStateOf(true) }
    val showBottomBar = (selectedTab != 0) || chatTabAtRoot
    val tabs = listOf(
        MainTab.Chat,
        MainTab.Overview,
        MainTab.Token,
        MainTab.Settings,
    )

    Scaffold(
        bottomBar = {
            if (showBottomBar) {
                NavigationBar {
                    tabs.forEachIndexed { index, tab ->
                        val label = AppStrings.get(lang, tab.labelKey)
                        NavigationBarItem(
                            icon = { Icon(tab.icon, contentDescription = label) },
                            label = { Text(label) },
                            selected = selectedTab == index,
                            onClick = { selectedTab = index },
                        )
                    }
                }
            }
        },
    ) { paddingValues ->
        Box(modifier = Modifier.padding(paddingValues)) {
            when (selectedTab) {
                0 -> ChatTab(navController = navController, onAtRootChange = { chatTabAtRoot = it })
                1 -> OverviewTab()
                2 -> TokenTab()
                3 -> SettingsTab(mainNavController = navController, onLogout = onLogout)
                else -> ChatTab(navController = navController, onAtRootChange = { chatTabAtRoot = it })
            }
        }
    }
}

enum class MainTab(
    val route: String,
    val labelKey: String,
    val icon: androidx.compose.ui.graphics.vector.ImageVector,
) {
    Chat("chat", "tab_chat", Icons.Default.Chat),
    Overview("overview", "tab_overview", Icons.Default.Person),
    Token("token", "tab_token", Icons.Default.Key),
    Settings("settings", "tab_settings", Icons.Default.Settings),
}
