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

package com.example.wificensor.sensing


import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.net.wifi.WifiManager
import android.os.Build
import com.example.wificensor.data.RssiSnapshot
import com.example.wificensor.data.WifiCensorDatabase
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Manages Wi-Fi scanning using WifiManager.
 *
 * Android throttling policy (as of Android 10+):
 *  - Background: max 4 scans / 2 minutes
 *  - Foreground app: max 4 scans / 2 minutes
 *  - With CHANGE_WIFI_STATE permission in a Foreground Service: fewer restrictions
 *
 * Strategy: Register a BroadcastReceiver for SCAN_RESULTS_AVAILABLE_ACTION and
 * call startScan() on a coroutine loop. On devices that throttle, the OS still
 * delivers cached results (~every 30s).
 */
class WifiScanner(private val context: Context) {

    data class ScanEntry(
        val bssid: String,
        val ssid: String,
        val rssi: Int,
        val frequency: Int,
        val timestamp: Long = System.currentTimeMillis()
    )

    private val wifiManager: WifiManager =
        context.applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager

    private val _scanResults = MutableStateFlow<List<ScanEntry>>(emptyList())
    val scanResults: StateFlow<List<ScanEntry>> = _scanResults.asStateFlow()

    private var scanJob: Job? = null
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private val db by lazy { WifiCensorDatabase.getInstance(context) }

    private val scanReceiver = object : BroadcastReceiver() {
        override fun onReceive(ctx: Context?, intent: Intent?) {
            if (intent?.action != WifiManager.SCAN_RESULTS_AVAILABLE_ACTION) return
            val success = intent.getBooleanExtra(WifiManager.EXTRA_RESULTS_UPDATED, false)
            if (success || wifiManager.scanResults.isNotEmpty()) {
                processScanResults()
            }
        }
    }

    fun start() {
        val filter = IntentFilter(WifiManager.SCAN_RESULTS_AVAILABLE_ACTION)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            context.registerReceiver(scanReceiver, filter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            @Suppress("UnspecifiedRegisterReceiverFlag")
            context.registerReceiver(scanReceiver, filter)
        }
        scheduleScan()
    }

    fun stop() {
        try { context.unregisterReceiver(scanReceiver) } catch (_: Exception) {}
        scanJob?.cancel()
        scope.cancel()
    }

    private fun scheduleScan() {
        scanJob = scope.launch {
            while (isActive) {
                @Suppress("DEPRECATION")
                wifiManager.startScan()     // deprecated but still the only option without root
                delay(SCAN_INTERVAL_MS)
            }
        }
    }

    private fun processScanResults() {
        scope.launch {
            @Suppress("DEPRECATION")
            val rawResults = wifiManager.scanResults
            val now = System.currentTimeMillis()
            val entries = rawResults.map { sr ->
                ScanEntry(
                    bssid     = sr.BSSID ?: "00:00:00:00:00:00",
                    ssid      = sr.SSID  ?: "<hidden>",
                    rssi      = sr.level,
                    frequency = sr.frequency,
                    timestamp = now
                )
            }
            _scanResults.value = entries

            // Persist to Room DB (keep only the strongest AP per scan cycle)
            val topEntries = entries
                .sortedByDescending { it.rssi }
                .take(MAX_APS_TO_STORE)
                .map { e ->
                    RssiSnapshot(
                        timestamp     = now,
                        bssid         = e.bssid,
                        ssid          = e.ssid,
                        rssi          = e.rssi,
                        frequency     = e.frequency,
                    )
                }
            db.rssiDao().insertAll(topEntries)

            // Prune data older than 30 days
            val thirtyDaysAgo = now - 30L * 24 * 60 * 60 * 1000
            db.rssiDao().deleteOlderThan(thirtyDaysAgo)
        }
    }

    companion object {
        const val SCAN_INTERVAL_MS  = 2_000L   // 2 seconds between scan requests
        const val MAX_APS_TO_STORE  = 5        // store top-5 APs per scan
    }
}
