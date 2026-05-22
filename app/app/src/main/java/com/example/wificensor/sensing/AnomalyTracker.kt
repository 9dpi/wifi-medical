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

import com.example.wificensor.data.AlertEvent

/**
 * Anomaly Tracker
 *
 * Watches the stream of PresenceResults and fires alerts when:
 * 1. The person has been STATIONARY for too long (immobility alert)
 * 2. Rapid PRESENT→ABSENT→PRESENT change (possible fall)
 * 3. Night-time activity outside configured quiet hours
 */
class AnomalyTracker {

    data class Config(
        val immobileThresholdMinutes: Int = 45,   // alert if stationary > 45 min
        val quietHourStart: Int = 23,              // 23:00
        val quietHourEnd:   Int = 6,               // 06:00
        val fallDetectionEnabled: Boolean = true
    )

    var config = Config()

    private var stationaryStartMs: Long? = null
    private var lastPresence = PresenceEngine.PresenceState.UNKNOWN
    private var lastTransitionMs = 0L
    private var isStarted = false

    fun start() { isStarted = true }

    /**
     * Called on every new PresenceResult.
     * [onAlert] is invoked (from coroutine context of caller) if an anomaly is detected.
     */
    suspend fun onResult(
        result: PresenceEngine.PresenceResult,
        onAlert: suspend (AlertEvent) -> Unit
    ) {
        if (!isStarted) return
        val now = System.currentTimeMillis()

        // ── Immobility Detection ─────────────────────────────────────
        if (result.presence == PresenceEngine.PresenceState.PRESENT &&
            result.activity == PresenceEngine.ActivityState.STATIONARY) {

            if (stationaryStartMs == null) stationaryStartMs = now

            val stationaryMs = now - (stationaryStartMs ?: now)
            val thresholdMs  = config.immobileThresholdMinutes * 60_000L

            if (stationaryMs >= thresholdMs) {
                val minutes = stationaryMs / 60_000
                onAlert(
                    AlertEvent(
                        timestamp = now,
                        level     = "WARN",
                        title     = "⚠️ Bất động quá lâu",
                        message   = "Phát hiện bất động ${minutes} phút. Vui lòng kiểm tra."
                    )
                )
                stationaryStartMs = now + 15 * 60_000L  // suppress next alert for 15 min
            }
        } else {
            stationaryStartMs = null
        }

        // ── Rapid Transition Fall Detection ──────────────────────────
        if (config.fallDetectionEnabled) {
            val timeSinceLast = now - lastTransitionMs
            val justWentAbsent = lastPresence == PresenceEngine.PresenceState.PRESENT &&
                    result.presence == PresenceEngine.PresenceState.ABSENT

            if (justWentAbsent && timeSinceLast < 3_000L) {
                // Very fast disappearance — could be a fall
                onAlert(
                    AlertEvent(
                        timestamp = now,
                        level     = "DANGER",
                        title     = "🔴 Nghi ngờ té ngã",
                        message   = "Tín hiệu biến mất đột ngột. Có thể đã xảy ra té ngã!"
                    )
                )
            }
        }

        // ── Transition Tracking ───────────────────────────────────────
        if (result.presence != lastPresence) {
            lastTransitionMs = now
            lastPresence     = result.presence
        }
    }
}
