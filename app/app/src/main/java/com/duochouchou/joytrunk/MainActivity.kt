package com.duochouchou.joytrunk

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import com.duochouchou.joytrunk.ui.JoyTrunkNavHost
import com.duochouchou.joytrunk.ui.locale.LocalAppLanguage
import com.duochouchou.joytrunk.ui.theme.JoyTrunkTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val app = application as JoyTrunkApplication
        setContent {
            val darkTheme by app.settingsRepository.darkTheme.collectAsState(initial = false)
            val language by app.settingsRepository.language.collectAsState(initial = "zh")
            CompositionLocalProvider(LocalAppLanguage provides language) {
                JoyTrunkTheme(darkTheme = darkTheme) {
                    JoyTrunkNavHost(app = app)
                }
            }
        }
    }
}
