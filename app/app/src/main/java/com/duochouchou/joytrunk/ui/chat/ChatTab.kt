package com.duochouchou.joytrunk.ui.chat

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.duochouchou.joytrunk.ui.nav.Routes

@Composable
fun ChatTab(
    navController: NavHostController = rememberNavController(),
    onAtRootChange: (Boolean) -> Unit = {},
) {
    val backStackEntry by navController.currentBackStackEntryAsState()
    LaunchedEffect(backStackEntry) {
        val atRoot = backStackEntry?.destination?.route == Routes.CHAT_LIST
        onAtRootChange(atRoot)
    }
    NavHost(
        navController = navController,
        startDestination = Routes.CHAT_LIST,
        modifier = Modifier.fillMaxSize(),
    ) {
        composable(Routes.CHAT_LIST) {
            ConversationListScreen(
                onConversationClick = { id -> navController.navigate("${Routes.CHAT_DETAIL}/$id") },
                onNewConversationClick = { navController.navigate(Routes.CREATE_CHAT_SELECT_EMPLOYEE) },
            )
        }
        composable("${Routes.CHAT_DETAIL}/{conversationId}") { backStackEntry ->
            val id = backStackEntry.arguments?.getString("conversationId")?.toIntOrNull() ?: 0
            ChatDetailScreen(
                conversationId = id,
                onBack = { navController.popBackStack() },
            )
        }
        composable(Routes.CREATE_CHAT_SELECT_EMPLOYEE) {
            CreateConversationScreen(
                onCreated = { convId ->
                    navController.navigate("${Routes.CHAT_DETAIL}/$convId") { popUpTo(Routes.CHAT_LIST) { inclusive = false } }
                },
                onBack = { navController.popBackStack() },
            )
        }
    }
}
