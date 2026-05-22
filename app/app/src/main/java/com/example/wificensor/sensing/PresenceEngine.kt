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

import com.example.wificensor.sensing.WifiScanner.ScanEntry
import kotlinx.coroutines.flow.*
import kotlin.math.pow
import kotlin.math.sqrt

/**
 * Presence Detection Engine — RSSI Variance Method
 *
 * Core insight:
 *  • When a person is present and moving → multipath interference →
 *    RSSI fluctuates significantly (high variance)
 *  • When room is empty → stable signal → low variance
 *
 * Algorithm:
 *  1. Collect RSSI samples in a sliding window (30s)
 *  2. Compute variance of the strongest AP's RSSI
 *  3. Compare against adaptive thresholds
 *  4. Output: PresenceState with confidence
 *
 * Adaptive thresholds:
 *  - Calibration phase learns the "baseline empty room" variance
 *  - After calibration, thresholds auto-adjust to environment noise floor
 */
class PresenceEngine {

    enum class PresenceState { PRESENT, ABSENT, UNKNOWN }
    enum class ActivityState  { WALKING, STATIONARY, SLEEPING, MOVING, UNKNOWN }

    data class PresenceResult(
        val presence:    PresenceState,
        val activity:    ActivityState,
        val confidence:  Float,           // 0.0 – 1.0
        val rssiVariance: Float,
        val rssiMean:     Float,
        val dominantBssid: String
    )

    // Sliding window of RSSI values per BSSID
    private val windowMs        = 30_000L         // 30-second window
    private val rssiWindow      = ArrayDeque<Pair<Long, Int>>()   // timestamp → rssi

    // Adaptive thresholds (recalibrated during calibration phase)
    private var baselineVariance = 0.5f            // calibrated "empty room" variance
    private var calibrated       = false
    private val calibSamples     = mutableListOf<Float>()

    // Threshold multipliers
    private val presenceThresholdMultiplier = 3.0f  // variance > 3× baseline = present
    private val movingThresholdMultiplier   = 8.0f  // variance > 8× baseline = moving

    fun process(scanList: List<ScanEntry>): PresenceResult {
        val now = System.currentTimeMillis()

        // Pick the strongest AP as the reference signal
        val best = scanList.maxByOrNull { it.rssi }
            ?: return PresenceResult(PresenceState.UNKNOWN, ActivityState.UNKNOWN, 0f, 0f, 0f, "")

        // Add to window
        rssiWindow.addLast(now to best.rssi)

        // Prune old samples outside the window
        while (rssiWindow.isNotEmpty() && (now - rssiWindow.first().first) > windowMs) {
            rssiWindow.removeFirst()
        }

        // Need minimum samples
        if (rssiWindow.size < MIN_SAMPLES) {
            return PresenceResult(PresenceState.UNKNOWN, ActivityState.UNKNOWN, 0f, 0f, best.rssi.toFloat(), best.bssid)
        }

        val values   = rssiWindow.map { it.second.toFloat() }
        val mean     = values.average().toFloat()
        val variance = computeVariance(values, mean)

        // Calibration phase: first 60 samples with no movement
        if (!calibrated) {
            calibSamples.add(variance)
            if (calibSamples.size >= CALIB_SAMPLES_REQUIRED) {
                baselineVariance = calibSamples.average().toFloat().coerceAtLeast(0.1f)
                calibrated = true
                calibSamples.clear()
            }
            return PresenceResult(PresenceState.UNKNOWN, ActivityState.UNKNOWN, 0f, variance, mean, best.bssid)
        }

        // Determine presence and activity
        val presenceThresh = baselineVariance * presenceThresholdMultiplier
        val movingThresh   = baselineVariance * movingThresholdMultiplier

        val (presence, activity, confidence) = when {
            variance >= movingThresh   -> Triple(PresenceState.PRESENT, ActivityState.WALKING,     computeConfidence(variance, movingThresh,   movingThresh * 3))
            variance >= presenceThresh -> Triple(PresenceState.PRESENT, ActivityState.STATIONARY,  computeConfidence(variance, presenceThresh, movingThresh))
            else                       -> Triple(PresenceState.ABSENT,  ActivityState.UNKNOWN,     computeConfidence(presenceThresh - variance, 0f, presenceThresh))
        }

        // Detect possible sleep (very low RSSI variance but present for a long time)
        val finalActivity = if (
            presence == PresenceState.PRESENT &&
            activity == ActivityState.STATIONARY &&
            variance < presenceThresh * 1.5f
        ) ActivityState.SLEEPING else activity

        return PresenceResult(
            presence      = presence,
            activity      = finalActivity,
            confidence    = confidence.coerceIn(0.3f, 0.99f),
            rssiVariance  = variance,
            rssiMean      = mean,
            dominantBssid = best.bssid
        )
    }

    /** Returns current calibration progress (0.0 – 1.0) */
    fun calibrationProgress(): Float =
        if (calibrated) 1f
        else calibSamples.size.toFloat() / CALIB_SAMPLES_REQUIRED

    /** Force recalibration (e.g., when user leaves the room manually) */
    fun recalibrate() {
        calibrated = false
        calibSamples.clear()
        rssiWindow.clear()
    }

    /** Override baseline if user confirms empty room */
    fun setBaseline(variance: Float) {
        baselineVariance = variance.coerceAtLeast(0.1f)
        calibrated = true
    }

    // ── Helpers ──────────────────────────────────────────────────────

    private fun computeVariance(values: List<Float>, mean: Float): Float {
        if (values.size < 2) return 0f
        val sumSq = values.sumOf { ((it - mean).toDouble().pow(2)) }
        return (sumSq / values.size).toFloat()
    }

    private fun computeConfidence(value: Float, low: Float, high: Float): Float {
        if (high <= low) return 0.5f
        return ((value - low) / (high - low)).toFloat().coerceIn(0f, 1f)
    }

    companion object {
        const val MIN_SAMPLES             = 8
        const val CALIB_SAMPLES_REQUIRED  = 30
    }
}
