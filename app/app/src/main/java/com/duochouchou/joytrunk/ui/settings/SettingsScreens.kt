package com.duochouchou.joytrunk.ui.settings

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material.icons.filled.Language
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Logout
import androidx.compose.material.icons.filled.Palette
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.duochouchou.joytrunk.JoyTrunkApplication
import com.duochouchou.joytrunk.ui.locale.AppStrings
import com.duochouchou.joytrunk.ui.locale.LocalAppLanguage
import com.duochouchou.joytrunk.ui.nav.Routes

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsTab(mainNavController: NavController, onLogout: () -> Unit) {
    val app = LocalContext.current.applicationContext as? JoyTrunkApplication ?: return
    val navController = rememberNavController()

    NavHost(
        navController = navController,
        startDestination = Routes.SETTINGS_LIST,
        modifier = Modifier.fillMaxSize(),
    ) {
        composable(Routes.SETTINGS_LIST) {
            val vm: SettingsViewModel = viewModel(
                factory = androidx.lifecycle.ViewModelProvider.AndroidViewModelFactory.getInstance(app),
            )
            SettingsListScreen(
                onNavigateToProfile = { navController.navigate(Routes.SETTINGS_PROFILE) },
                onNavigateToLanguage = { navController.navigate(Routes.SETTINGS_LANGUAGE) },
                onNavigateToTheme = { navController.navigate(Routes.SETTINGS_THEME) },
                onNavigateToPassword = { navController.navigate(Routes.SETTINGS_PASSWORD) },
                onLogout = {
                    vm.logout()
                    onLogout()
                },
            )
        }
        composable(Routes.SETTINGS_PROFILE) {
            ProfileSettingsScreen(
                onBack = { navController.popBackStack() },
                viewModel = viewModel(factory = androidx.lifecycle.ViewModelProvider.AndroidViewModelFactory.getInstance(app)),
            )
        }
        composable(Routes.SETTINGS_LANGUAGE) {
            LanguageSettingsScreen(
                onBack = { navController.popBackStack() },
                viewModel = viewModel(factory = androidx.lifecycle.ViewModelProvider.AndroidViewModelFactory.getInstance(app)),
            )
        }
        composable(Routes.SETTINGS_THEME) {
            ThemeSettingsScreen(
                onBack = { navController.popBackStack() },
                viewModel = viewModel(factory = androidx.lifecycle.ViewModelProvider.AndroidViewModelFactory.getInstance(app)),
            )
        }
        composable(Routes.SETTINGS_PASSWORD) {
            PasswordSettingsScreen(
                onBack = { navController.popBackStack() },
                viewModel = viewModel(factory = androidx.lifecycle.ViewModelProvider.AndroidViewModelFactory.getInstance(app)),
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun SettingsListScreen(
    onNavigateToProfile: () -> Unit,
    onNavigateToLanguage: () -> Unit,
    onNavigateToTheme: () -> Unit,
    onNavigateToPassword: () -> Unit,
    onLogout: () -> Unit,
) {
    val lang = LocalAppLanguage.current
    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text(AppStrings.get(lang, "settings"), style = MaterialTheme.typography.titleLarge) },
                colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                    titleContentColor = MaterialTheme.colorScheme.onSurface,
                ),
            )
        },
    ) { paddingValues ->
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(paddingValues)
                .padding(horizontal = 16.dp, vertical = 12.dp),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surface,
                contentColor = MaterialTheme.colorScheme.onSurface,
            ),
            shape = RoundedCornerShape(16.dp),
            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
        ) {
            Column {
                SettingsListItem(
                    icon = Icons.Default.Person,
                    title = AppStrings.get(lang, "profile"),
                    onClick = onNavigateToProfile,
                )
                HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp), color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f))
                SettingsListItem(icon = Icons.Default.Language, title = AppStrings.get(lang, "language"), onClick = onNavigateToLanguage)
                HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp), color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f))
                SettingsListItem(icon = Icons.Default.Palette, title = AppStrings.get(lang, "theme"), onClick = onNavigateToTheme)
                HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp), color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f))
                SettingsListItem(icon = Icons.Default.Lock, title = AppStrings.get(lang, "password"), onClick = onNavigateToPassword)
                HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp), color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f))
                SettingsListItem(
                    icon = Icons.Default.Logout,
                    title = AppStrings.get(lang, "logout"),
                    onClick = onLogout,
                    showChevron = false,
                    titleColor = MaterialTheme.colorScheme.error,
                )
            }
        }
    }
}

@Composable
private fun SettingsListItem(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    title: String,
    onClick: () -> Unit,
    showChevron: Boolean = true,
    titleColor: androidx.compose.ui.graphics.Color = MaterialTheme.colorScheme.onSurface,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(16.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(
            icon,
            contentDescription = null,
            modifier = Modifier.size(24.dp),
            tint = if (titleColor == MaterialTheme.colorScheme.error) titleColor else MaterialTheme.colorScheme.primary,
        )
        Text(
            text = title,
            style = MaterialTheme.typography.bodyLarge,
            color = titleColor,
            modifier = Modifier.weight(1f).padding(horizontal = 16.dp),
        )
        if (showChevron) {
            Icon(
                Icons.Default.ChevronRight,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ProfileSettingsScreen(
    onBack: () -> Unit,
    viewModel: SettingsViewModel,
) {
    val state by viewModel.state.collectAsState()
    val lang = LocalAppLanguage.current
    LaunchedEffect(Unit) { viewModel.load() }

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text(AppStrings.get(lang, "profile"), style = MaterialTheme.typography.titleLarge) },
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
        },
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            state.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            if (state.saveSuccess) Text(AppStrings.get(lang, "saved"), color = MaterialTheme.colorScheme.primary)

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
                    OutlinedTextField(
                        value = state.name,
                        onValueChange = { viewModel.updateName(it) },
                        label = { Text(AppStrings.get(lang, "nickname")) },
                        modifier = Modifier.fillMaxWidth(),
                    )
                    OutlinedTextField(
                        value = state.avatarUrl,
                        onValueChange = { viewModel.updateAvatarUrl(it) },
                        label = { Text(AppStrings.get(lang, "avatar_url")) },
                        modifier = Modifier.fillMaxWidth().padding(top = 12.dp),
                    )
                    androidx.compose.material3.Button(
                        onClick = { viewModel.saveProfile() },
                        modifier = Modifier.fillMaxWidth().padding(top = 20.dp),
                    ) {
                        Text(AppStrings.get(lang, "save"))
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun LanguageSettingsScreen(
    onBack: () -> Unit,
    viewModel: SettingsViewModel,
) {
    val state by viewModel.state.collectAsState()
    val lang = LocalAppLanguage.current

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text(AppStrings.get(lang, "language"), style = MaterialTheme.typography.titleLarge) },
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
        },
    ) { paddingValues ->
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(paddingValues)
                .padding(20.dp),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surface,
                contentColor = MaterialTheme.colorScheme.onSurface,
            ),
            shape = RoundedCornerShape(16.dp),
            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
        ) {
            Column(Modifier.padding(16.dp)) {
                listOf("zh" to "language_zh", "en" to "language_en").forEach { (code, key) ->
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        RadioButton(
                            selected = state.language == code,
                            onClick = { viewModel.setLanguage(code) },
                        )
                        Text(AppStrings.get(lang, key), style = MaterialTheme.typography.bodyLarge)
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ThemeSettingsScreen(
    onBack: () -> Unit,
    viewModel: SettingsViewModel,
) {
    val state by viewModel.state.collectAsState()
    val lang = LocalAppLanguage.current

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text(AppStrings.get(lang, "theme"), style = MaterialTheme.typography.titleLarge) },
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
        },
    ) { paddingValues ->
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(paddingValues)
                .padding(20.dp),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surface,
                contentColor = MaterialTheme.colorScheme.onSurface,
            ),
            shape = RoundedCornerShape(16.dp),
            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(20.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(AppStrings.get(lang, "theme_dark"), style = MaterialTheme.typography.bodyLarge, modifier = Modifier.weight(1f))
                Switch(
                    checked = state.darkTheme,
                    onCheckedChange = { viewModel.setDarkTheme(it) },
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun PasswordSettingsScreen(
    onBack: () -> Unit,
    viewModel: SettingsViewModel,
) {
    val state by viewModel.state.collectAsState()
    val lang = LocalAppLanguage.current
    var oldPw by remember { mutableStateOf("") }
    var newPw by remember { mutableStateOf("") }

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text(AppStrings.get(lang, "password"), style = MaterialTheme.typography.titleLarge) },
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
        },
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            state.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            if (state.passwordSuccess) Text(AppStrings.get(lang, "password_changed"), color = MaterialTheme.colorScheme.primary)

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
                    OutlinedTextField(
                        value = oldPw,
                        onValueChange = { oldPw = it },
                        label = { Text(AppStrings.get(lang, "current_password")) },
                        modifier = Modifier.fillMaxWidth(),
                    )
                    OutlinedTextField(
                        value = newPw,
                        onValueChange = { newPw = it },
                        label = { Text(AppStrings.get(lang, "new_password")) },
                        modifier = Modifier.fillMaxWidth().padding(top = 12.dp),
                    )
                    androidx.compose.material3.Button(
                        onClick = {
                            viewModel.updatePassword(oldPw, newPw) { _, _ -> }
                        },
                        modifier = Modifier.fillMaxWidth().padding(top = 20.dp),
                    ) {
                        Text(AppStrings.get(lang, "change_password"))
                    }
                }
            }
        }
    }
}
