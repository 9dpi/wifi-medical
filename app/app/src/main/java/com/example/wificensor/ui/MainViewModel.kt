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

package com.example.wificensor.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.wificensor.data.AlertEvent
import com.example.wificensor.data.PresenceEvent
import com.example.wificensor.data.WifiCensorDatabase
import com.example.wificensor.sensing.PresenceEngine
import com.example.wificensor.sensing.SensingService
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

/**
 * Shared ViewModel providing live data to all screens.
 * Combines the SensingService StateFlow with Room DB flows.
 */
class MainViewModel(private val db: WifiCensorDatabase) : ViewModel() {

    // Live sensor result from the foreground service
    val liveResult: StateFlow<PresenceEngine.PresenceResult?> = SensingService.liveResult
    val isServiceRunning: StateFlow<Boolean>                  = SensingService.isRunning

    // Recent presence events from DB (for history)
    val recentEvents: StateFlow<List<PresenceEvent>> = db.presenceDao()
        .observeRecent(50)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    // Recent alerts
    val recentAlerts: StateFlow<List<AlertEvent>> = db.alertDao()
        .observeRecent()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    // Today's stats
    private val _stats = MutableStateFlow(Pair(0L, 0L))  // presentMin, absentMin
    val stats: StateFlow<Pair<Long, Long>> = _stats.asStateFlow()

    init {
        viewModelScope.launch {
            while (true) {
                refreshStats()
                kotlinx.coroutines.delay(60_000L)  // refresh every minute
            }
        }
    }

    private suspend fun refreshStats() {
        val now      = System.currentTimeMillis()
        val cal      = java.util.Calendar.getInstance().apply {
            timeInMillis = now
            set(java.util.Calendar.HOUR_OF_DAY, 0)
            set(java.util.Calendar.MINUTE, 0)
            set(java.util.Calendar.SECOND, 0)
        }
        val dayStart = cal.timeInMillis
        val present  = db.presenceDao().totalMinutesToday("PRESENT", dayStart, now) ?: 0
        val absent   = db.presenceDao().totalMinutesToday("ABSENT",  dayStart, now) ?: 0
        _stats.value = Pair(present, absent)
    }

    fun acknowledgeAlert(id: Long) {
        viewModelScope.launch { db.alertDao().acknowledge(id) }
    }
}

class MainViewModelFactory(private val db: WifiCensorDatabase) :
    androidx.lifecycle.ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T = MainViewModel(db) as T
}
