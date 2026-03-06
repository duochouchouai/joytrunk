package com.duochouchou.joytrunk.ui.chat

import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.duochouchou.joytrunk.JoyTrunkApplication
import com.duochouchou.joytrunk.ui.locale.AppStrings
import com.duochouchou.joytrunk.ui.locale.LocalAppLanguage

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CreateConversationScreen(
    onCreated: (Int) -> Unit,
    onBack: () -> Unit,
) {
    val app = LocalContext.current.applicationContext as? JoyTrunkApplication ?: return
    val viewModel: CreateConversationViewModel = viewModel(
        factory = androidx.lifecycle.ViewModelProvider.AndroidViewModelFactory.getInstance(app),
    )
    val state by viewModel.state.collectAsState()
    val lang = LocalAppLanguage.current
    LaunchedEffect(Unit) { viewModel.loadEmployees() }

    Column(Modifier.fillMaxSize()) {
        TopAppBar(
            title = { Text(AppStrings.get(lang, "select_employee")) },
            navigationIcon = {
                IconButton(onClick = onBack) {
                    Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = AppStrings.get(lang, "back"))
                }
            },
        )
        state.error?.let { Text(it, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(16.dp)) }
        if (state.loading && state.employees.isEmpty()) {
            CircularProgressIndicator(Modifier.padding(16.dp))
        }
        if (state.employees.isEmpty() && !state.loading) {
            Text(
                AppStrings.get(lang, "no_employee_hint"),
                modifier = Modifier.padding(16.dp),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        LazyColumn(
            modifier = Modifier.weight(1f).fillMaxWidth(),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp),
        ) {
            items(state.employees) { emp ->
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 4.dp)
                        .clickable { viewModel.selectEmployee(emp.id) },
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surface,
                        contentColor = MaterialTheme.colorScheme.onSurface,
                    ),
                ) {
                    androidx.compose.foundation.layout.Row(
                        modifier = Modifier.padding(16.dp),
                        verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
                    ) {
                        RadioButton(
                            selected = state.selectedEmployeeId == emp.id,
                            onClick = { viewModel.selectEmployee(emp.id) },
                        )
                        Text(
                            text = emp.name ?: emp.id,
                            style = MaterialTheme.typography.bodyLarge,
                            modifier = Modifier.padding(start = 8.dp),
                        )
                    }
                }
            }
        }
        Spacer(Modifier.height(16.dp))
        Button(
            onClick = { viewModel.createConversation(onCreated) },
            modifier = Modifier.fillMaxWidth().padding(16.dp),
            enabled = state.selectedEmployeeId != null && !state.creating,
        ) {
            Text(if (state.creating) AppStrings.get(lang, "creating") else AppStrings.get(lang, "create_conversation"))
        }
    }
}
