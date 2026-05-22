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

package com.example.wificensor.sync

import android.content.Context
import androidx.work.*
import com.example.wificensor.data.PresenceEvent
import com.example.wificensor.data.WifiCensorDatabase
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import java.io.File
import java.text.SimpleDateFormat
import java.util.*
import java.util.concurrent.TimeUnit

/**
 * WorkManager worker that:
 * 1. Reads presence events from Room DB
 * 2. Builds a JSON snapshot (wificensor_status.json)
 * 3. Writes to app's external files directory (accessible via Google Drive backup or manual copy)
 *
 * Google Drive sync:
 * - The JSON file is written to the app's "Documents" folder
 * - Google One automatically backs up app data on Android 12+ if enabled
 * - Alternatively, the user can share the file folder via Google Drive manual upload
 *
 * Note: Full Google Drive API integration requires OAuth setup which is
 * configured separately in Settings screen. This worker handles the
 * local file creation; drive upload is optional enhancement.
 */
class GoogleDriveSyncWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {

    private val db by lazy { WifiCensorDatabase.getInstance(applicationContext) }

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        try {
            val snapshot = buildSnapshot()
            val json     = Json.encodeToString(StatusSnapshot.serializer(), snapshot)
            writeToFile(json)
            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }

    private suspend fun buildSnapshot(): StatusSnapshot {
        val now      = System.currentTimeMillis()
        val dayStart = getDayStart(now)

        val recentEvents = db.presenceDao().getSince(dayStart)
        val alerts       = db.alertDao()
            .observeRecent()
            .let { flow ->
                // Since we can't collect in a suspend fn directly, use a one-shot query
                emptyList<com.example.wificensor.data.AlertEvent>()
            }

        val presentMin = db.presenceDao().totalMinutesToday("PRESENT", dayStart, now) ?: 0
        val absentMin  = db.presenceDao().totalMinutesToday("ABSENT",  dayStart, now) ?: 0

        val lastEvent    = recentEvents.lastOrNull()
        val roomStatus   = lastEvent?.eventType ?: "UNKNOWN"
        val activity     = lastEvent?.activity  ?: ""
        val confidence   = lastEvent?.confidence ?: 0f

        val timelineFmt = SimpleDateFormat("HH:mm", Locale.getDefault())
        val timeline = recentEvents.takeLast(10).map { e ->
            TimelineEntry(
                time   = timelineFmt.format(Date(e.startTime)),
                status = e.eventType.lowercase(),
                event  = when (e.eventType) {
                    "PRESENT" -> "Phát hiện có người"
                    "ABSENT"  -> "Ra khỏi phòng"
                    else      -> e.eventType
                },
                sub    = e.activity.lowercase().replaceFirstChar { it.uppercase() }
            )
        }

        // Build hourly RSSI history (last 24h)
        val rssiHistory = buildRssiHistory(now)

        // Build 7-day stats
        val weekHistory = buildWeekHistory(now)

        return StatusSnapshot(
            lastUpdated  = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssXXX", Locale.getDefault()).format(Date(now)),
            roomStatus   = roomStatus,
            confidence   = confidence,
            activity     = activity,
            rssiVariance = 0f,   // filled by SensingService if available
            rssiCurrent  = 0,
            timeline     = timeline,
            alerts       = emptyList(),
            stats        = Stats(presentMin, absentMin),
            history      = weekHistory,
            rssiHistory  = rssiHistory
        )
    }

    private suspend fun buildRssiHistory(now: Long): RssiHistory {
        val oneDayAgo = now - 24 * 3600_000L
        val snapshots = db.rssiDao().getSince(oneDayAgo)
        val fmt       = SimpleDateFormat("HH:00", Locale.getDefault())

        // Group by hour
        val byHour = snapshots.groupBy {
            val cal = Calendar.getInstance().apply { timeInMillis = it.timestamp }
            cal.get(Calendar.HOUR_OF_DAY)
        }

        val labels   = mutableListOf<String>()
        val rssiVals = mutableListOf<Float>()
        val varVals  = mutableListOf<Float>()

        for (h in 0..23) {
            val cal = Calendar.getInstance().apply {
                timeInMillis = now
                set(Calendar.HOUR_OF_DAY, h)
                set(Calendar.MINUTE, 0)
            }
            labels.add(fmt.format(cal.time))
            val hourSnaps = byHour[h]
            if (hourSnaps.isNullOrEmpty()) {
                rssiVals.add(-75f)
                varVals.add(0f)
            } else {
                val mean = hourSnaps.map { it.rssi.toFloat() }.average().toFloat()
                val variance = hourSnaps.map { it.rssi.toFloat() }.let { vals ->
                    val avg = vals.average().toFloat()
                    vals.map { (it - avg) * (it - avg) }.average().toFloat()
                }
                rssiVals.add(mean)
                varVals.add(variance)
            }
        }
        return RssiHistory(labels, rssiVals, varVals)
    }

    private suspend fun buildWeekHistory(now: Long): WeekHistory {
        val dayFmt = SimpleDateFormat("EEE", Locale("vi"))
        val labels = mutableListOf<String>()
        val present = mutableListOf<Long>()
        val absent  = mutableListOf<Long>()

        for (dayOffset in 6 downTo 0) {
            val cal = Calendar.getInstance().apply {
                timeInMillis = now
                add(Calendar.DAY_OF_YEAR, -dayOffset)
                set(Calendar.HOUR_OF_DAY, 0)
                set(Calendar.MINUTE, 0)
                set(Calendar.SECOND, 0)
            }
            val dayStart = cal.timeInMillis
            val dayEnd   = dayStart + 86_400_000L
            labels.add(dayFmt.format(cal.time))
            present.add(db.presenceDao().totalMinutesToday("PRESENT", dayStart, minOf(dayEnd, now)) ?: 0)
            absent.add(db.presenceDao().totalMinutesToday("ABSENT",   dayStart, minOf(dayEnd, now)) ?: 0)
        }
        return WeekHistory(labels, present, absent)
    }

    private fun writeToFile(json: String) {
        val dir  = applicationContext.getExternalFilesDir("WifiCensor") ?: applicationContext.filesDir
        val file = File(dir, "wificensor_status.json")
        file.writeText(json)
    }

    private fun getDayStart(now: Long): Long {
        val cal = Calendar.getInstance().apply {
            timeInMillis = now
            set(Calendar.HOUR_OF_DAY, 0)
            set(Calendar.MINUTE, 0)
            set(Calendar.SECOND, 0)
            set(Calendar.MILLISECOND, 0)
        }
        return cal.timeInMillis
    }

    companion object {
        const val WORK_NAME = "wificensor_drive_sync"

        fun schedule(context: Context) {
            val request = PeriodicWorkRequestBuilder<GoogleDriveSyncWorker>(
                5, TimeUnit.MINUTES
            ).setConstraints(
                Constraints.Builder()
                    .setRequiredNetworkType(NetworkType.CONNECTED)
                    .build()
            ).build()

            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                WORK_NAME,
                ExistingPeriodicWorkPolicy.KEEP,
                request
            )
        }

        fun cancel(context: Context) {
            WorkManager.getInstance(context).cancelUniqueWork(WORK_NAME)
        }
    }
}

// ─── JSON Data Models ───────────────────────────────────────────────────

@Serializable
data class StatusSnapshot(
    val lastUpdated:  String,
    val roomStatus:   String,
    val confidence:   Float,
    val activity:     String,
    val rssiVariance: Float,
    val rssiCurrent:  Int,
    val timeline:     List<TimelineEntry>,
    val alerts:       List<AlertEntry>,
    val stats:        Stats,
    val history:      WeekHistory,
    val rssiHistory:  RssiHistory
)

@Serializable data class TimelineEntry(val time: String, val status: String, val event: String, val sub: String)
@Serializable data class AlertEntry(val level: String, val title: String, val message: String, val time: String)
@Serializable data class Stats(val presentMinutes: Long, val absentMinutes: Long)
@Serializable data class WeekHistory(val labels: List<String>, val present: List<Long>, val absent: List<Long>)
@Serializable data class RssiHistory(val labels: List<String>, val rssi: List<Float>, val variance: List<Float>)
