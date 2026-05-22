/*
 * Copyright 2025 - 2026 Vu Quang Cuong
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.example.wificensor.ui.main

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation3.runtime.NavKey
import com.example.wificensor.data.WifiCensorDatabase
import com.example.wificensor.ui.DashboardScreen
import com.example.wificensor.ui.HistoryScreen
import com.example.wificensor.ui.SettingsScreen
import com.example.wificensor.ui.MainViewModel
import com.example.wificensor.ui.MainViewModelFactory

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
  onItemClick: (NavKey) -> Unit,
  modifier: Modifier = Modifier,
) {
  var selectedTab by remember { mutableIntStateOf(0) }
  
  val context = LocalContext.current
  val db = WifiCensorDatabase.getInstance(context)
  val vm: MainViewModel = viewModel(factory = MainViewModelFactory(db))
  val events by vm.recentEvents.collectAsStateWithLifecycle()

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
        1 -> HistoryScreen(events = events)
        2 -> SettingsScreen()
      }
    }
  }
}


