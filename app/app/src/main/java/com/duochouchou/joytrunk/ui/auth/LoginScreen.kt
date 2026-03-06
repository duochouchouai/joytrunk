package com.duochouchou.joytrunk.ui.auth

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import com.duochouchou.joytrunk.ui.locale.AppStrings
import com.duochouchou.joytrunk.ui.locale.LocalAppLanguage

@Composable
fun LoginScreen(
    onLoginSuccess: () -> Unit,
    onGoToRegister: () -> Unit = {},
    viewModel: AuthViewModel,
    strings: AuthStrings,
) {
    val uiState by viewModel.uiState.collectAsState()
    if (uiState.loginSuccess) onLoginSuccess()

    var tabIndex by remember { mutableIntStateOf(0) }
    var phone by remember { mutableStateOf("") }
    var phoneCode by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var emailCode by remember { mutableStateOf("") }
    var account by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    val lang = LocalAppLanguage.current

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(24.dp)
            .verticalScroll(rememberScrollState()),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Spacer(modifier = Modifier.height(48.dp))
        Text(
            text = "JoyTrunk",
            style = MaterialTheme.typography.headlineLarge,
            color = MaterialTheme.colorScheme.primary,
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = strings.subtitle,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(modifier = Modifier.height(32.dp))

        TabRow(selectedTabIndex = tabIndex) {
            Tab(
                selected = tabIndex == 0,
                onClick = { tabIndex = 0; viewModel.clearError() },
                text = { Text(strings.tabPhone) },
            )
            Tab(
                selected = tabIndex == 1,
                onClick = { tabIndex = 1; viewModel.clearError() },
                text = { Text(strings.tabEmail) },
            )
            Tab(
                selected = tabIndex == 2,
                onClick = { tabIndex = 2; viewModel.clearError() },
                text = { Text(strings.tabPassword) },
            )
        }

        Spacer(modifier = Modifier.height(24.dp))

        when (tabIndex) {
            0 -> {
                OutlinedTextField(
                    value = phone,
                    onValueChange = { phone = it },
                    label = { Text(strings.phone) },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
                )
                Spacer(modifier = Modifier.height(12.dp))
                OutlinedTextField(
                    value = phoneCode,
                    onValueChange = { phoneCode = it },
                    label = { Text(strings.code) },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                )
                Spacer(modifier = Modifier.height(16.dp))
                Button(
                    onClick = { viewModel.sendPhoneCode(phone) },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !uiState.loading && phone.isNotBlank(),
                ) {
                    Text(strings.sendCode)
                }
                Spacer(modifier = Modifier.height(8.dp))
                Button(
                    onClick = { viewModel.loginByPhoneCode(phone, phoneCode) },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !uiState.loading && phone.isNotBlank() && phoneCode.isNotBlank(),
                ) {
                    Text(strings.login)
                }
            }
            1 -> {
                Text(
                    text = strings.emailRegisterHint,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(bottom = 8.dp),
                )
                OutlinedTextField(
                    value = email,
                    onValueChange = { email = it },
                    label = { Text(strings.email) },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                )
                Spacer(modifier = Modifier.height(12.dp))
                OutlinedTextField(
                    value = emailCode,
                    onValueChange = { emailCode = it },
                    label = { Text(strings.code) },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                )
                Spacer(modifier = Modifier.height(16.dp))
                Button(
                    onClick = { viewModel.sendEmailCode(email) },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !uiState.loading && email.isNotBlank(),
                ) {
                    Text(strings.sendCode)
                }
                Spacer(modifier = Modifier.height(8.dp))
                Button(
                    onClick = { viewModel.loginByEmailCode(email, emailCode) },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !uiState.loading && email.isNotBlank() && emailCode.isNotBlank(),
                ) {
                    Text(strings.login)
                }
            }
            2 -> {
                var passwordVisible by remember { mutableStateOf(false) }
                OutlinedTextField(
                    value = account,
                    onValueChange = { account = it },
                    label = { Text(strings.account) },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                Spacer(modifier = Modifier.height(12.dp))
                OutlinedTextField(
                    value = password,
                    onValueChange = { password = it },
                    label = { Text(strings.password) },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                    trailingIcon = {
                        IconButton(onClick = { passwordVisible = !passwordVisible }) {
                            Icon(
                                imageVector = if (passwordVisible) Icons.Default.VisibilityOff else Icons.Default.Visibility,
                                contentDescription = if (passwordVisible) AppStrings.get(lang, "hide_password") else AppStrings.get(lang, "show_password"),
                            )
                        }
                    },
                )
                Spacer(modifier = Modifier.height(16.dp))
                Button(
                    onClick = { viewModel.loginByPassword(account, password) },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !uiState.loading && account.isNotBlank() && password.isNotBlank(),
                ) {
                    Text(strings.login)
                }
            }
        }

        Spacer(modifier = Modifier.height(24.dp))
        TextButton(onClick = { tabIndex = 1 }) {
            Text(strings.goToRegister)
        }

        uiState.error?.let { err ->
            Spacer(modifier = Modifier.height(8.dp))
            Text(text = err, color = MaterialTheme.colorScheme.error)
        }
        if (uiState.loading) {
            Spacer(modifier = Modifier.height(16.dp))
            CircularProgressIndicator(modifier = Modifier.size(32.dp))
        }
    }
}

data class AuthStrings(
    val subtitle: String,
    val tabPhone: String,
    val tabEmail: String,
    val tabPassword: String,
    val phone: String,
    val email: String,
    val code: String,
    val account: String,
    val password: String,
    val sendCode: String,
    val login: String,
    val goToRegister: String,
    val emailRegisterHint: String,
)
