package com.example.wificensor.ui.main

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.navigation3.runtime.NavKey
import com.example.wificensor.ui.DashboardScreen

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
  onItemClick: (NavKey) -> Unit,
  modifier: Modifier = Modifier,
) {
  var selectedTab by remember { mutableIntStateOf(0) }

  Scaffold(
    bottomBar = {
      NavigationBar {
        NavigationBarItem(
          selected = selectedTab == 0,
          onClick  = { selectedTab = 0 },
          icon     = { Icon(Icons.Default.Home, null) },
          label    = { Text("Dashboard") }
        )
        NavigationBarItem(
          selected = selectedTab == 1,
          onClick  = { selectedTab = 1 },
          icon     = { Icon(Icons.Default.History, null) },
          label    = { Text("Lịch sử") }
        )
        NavigationBarItem(
          selected = selectedTab == 2,
          onClick  = { selectedTab = 2 },
          icon     = { Icon(Icons.Default.Settings, null) },
          label    = { Text("Cài đặt") }
        )
      }
    }
  ) { innerPadding ->
    Box(modifier = Modifier.fillMaxSize().padding(innerPadding)) {
      when (selectedTab) {
        0 -> DashboardScreen()
        1 -> HistoryPlaceholder()
        2 -> SettingsPlaceholder()
      }
    }
  }
}

@Composable
fun HistoryPlaceholder() {
  Box(Modifier.fillMaxSize(), contentAlignment = androidx.compose.ui.Alignment.Center) {
    Text("📋 Lịch sử — Đang xây dựng", style = MaterialTheme.typography.bodyLarge)
  }
}

@Composable
fun SettingsPlaceholder() {
  Box(Modifier.fillMaxSize(), contentAlignment = androidx.compose.ui.Alignment.Center) {
    Text("⚙️ Cài đặt — Đang xây dựng", style = MaterialTheme.typography.bodyLarge)
  }
}

