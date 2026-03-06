package com.duochouchou.joytrunk.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.runtime.getValue
import androidx.compose.runtime.collectAsState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.duochouchou.joytrunk.JoyTrunkApplication
import com.duochouchou.joytrunk.ui.auth.AuthStrings
import com.duochouchou.joytrunk.ui.auth.AuthViewModel
import com.duochouchou.joytrunk.ui.auth.LoginScreen
import com.duochouchou.joytrunk.ui.main.MainScreen
import com.duochouchou.joytrunk.ui.locale.AppStrings
import com.duochouchou.joytrunk.ui.locale.LocalAppLanguage
import com.duochouchou.joytrunk.ui.nav.Routes

@Composable
fun JoyTrunkNavHost(app: JoyTrunkApplication) {
    val navController = rememberNavController()
    remember { app.settingsRepository }
    val lang = LocalAppLanguage.current

    NavHost(
        navController = navController,
        startDestination = "splash",
    ) {
        composable("splash") {
            SplashScreen(app = app, navController = navController)
        }
        composable(Routes.LOGIN) {
            val authViewModel: AuthViewModel = viewModel(
                factory = androidx.lifecycle.ViewModelProvider.AndroidViewModelFactory.getInstance(app),
            )
            LoginScreen(
                onLoginSuccess = { navController.navigate(Routes.MAIN) { popUpTo(Routes.LOGIN) { inclusive = true } } },
                onGoToRegister = { },
                viewModel = authViewModel,
                strings = defaultAuthStrings(lang),
            )
        }
        composable(Routes.MAIN) {
            MainScreen(onLogout = { navController.navigate(Routes.LOGIN) { popUpTo(Routes.MAIN) { inclusive = true } } })
        }
    }
}

@Composable
private fun SplashScreen(app: JoyTrunkApplication, navController: NavController) {
    val lang = LocalAppLanguage.current
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        CircularProgressIndicator()
        Text(AppStrings.get(lang, "loading"))
    }
    LaunchedEffect(Unit) {
        val token = app.settingsRepository.tokenSync
        navController.navigate(if (!token.isNullOrEmpty()) Routes.MAIN else Routes.LOGIN) {
            popUpTo("splash") { inclusive = true }
        }
    }
}

private fun defaultAuthStrings(lang: String) = AuthStrings(
    subtitle = AppStrings.get(lang, "login_subtitle"),
    tabPhone = AppStrings.get(lang, "login_tab_phone"),
    tabEmail = AppStrings.get(lang, "login_tab_email"),
    tabPassword = AppStrings.get(lang, "login_tab_password"),
    phone = AppStrings.get(lang, "login_phone"),
    email = AppStrings.get(lang, "login_email"),
    code = AppStrings.get(lang, "login_code"),
    account = AppStrings.get(lang, "login_account"),
    password = AppStrings.get(lang, "login_password"),
    sendCode = AppStrings.get(lang, "login_send_code"),
    login = AppStrings.get(lang, "login"),
    goToRegister = AppStrings.get(lang, "go_to_register"),
    emailRegisterHint = AppStrings.get(lang, "email_register_hint"),
)
