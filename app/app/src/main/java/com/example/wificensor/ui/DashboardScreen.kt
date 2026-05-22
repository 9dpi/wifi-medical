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

import android.content.Intent
import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.*
import androidx.compose.foundation.shape.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.draw.*
import androidx.compose.ui.graphics.*
import androidx.compose.ui.platform.*
import androidx.compose.ui.text.font.*
import androidx.compose.ui.text.style.*
import androidx.compose.ui.unit.*
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.wificensor.data.WifiCensorDatabase
import com.example.wificensor.sensing.PresenceEngine
import com.example.wificensor.sensing.SensingService
import java.text.SimpleDateFormat
import java.util.*

// ─────────────────────────────────────────────────────────────────────────
//  Dashboard Screen  — Main presence monitoring view
// ─────────────────────────────────────────────────────────────────────────

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen() {
    val context = LocalContext.current
    val db      = WifiCensorDatabase.getInstance(context)
    val vm: MainViewModel = viewModel(factory = MainViewModelFactory(db))

    val result     by vm.liveResult.collectAsStateWithLifecycle()
    val isRunning  by vm.isServiceRunning.collectAsStateWithLifecycle()
    val alerts     by vm.recentAlerts.collectAsStateWithLifecycle()
    val events     by vm.recentEvents.collectAsStateWithLifecycle()
    val stats      by vm.stats.collectAsStateWithLifecycle()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .verticalScroll(rememberScrollState())
    ) {
        // ── Top bar ──────────────────────────────────────────────────
        TopBarSection(isRunning = isRunning, onToggle = {
            val intent = Intent(context, SensingService::class.java).apply {
                action = if (isRunning) SensingService.ACTION_STOP else SensingService.ACTION_START
            }
            context.startForegroundService(intent)
        })

        Spacer(Modifier.height(16.dp))

        // ── Status Hero Card ─────────────────────────────────────────
        StatusHeroCard(result = result, modifier = Modifier.padding(horizontal = 16.dp))

        Spacer(Modifier.height(16.dp))

        // ── Stats Row ────────────────────────────────────────────────
        StatsRow(
            presentMin  = stats.first,
            absentMin   = stats.second,
            rssiVariance = result?.rssiVariance ?: 0f,
            modifier    = Modifier.padding(horizontal = 16.dp)
        )

        Spacer(Modifier.height(16.dp))

        // ── Recent Activity ──────────────────────────────────────────
        SectionTitle("📋 Hoạt động hôm nay", modifier = Modifier.padding(horizontal = 16.dp))
        Spacer(Modifier.height(8.dp))

        if (events.isEmpty()) {
            EmptyStateCard(
                text     = "Chưa có dữ liệu. Hãy bật cảm biến.",
                modifier = Modifier.padding(horizontal = 16.dp)
            )
        } else {
            LazyColumn(
                modifier      = Modifier.height(280.dp).padding(horizontal = 16.dp),
                userScrollEnabled = true
            ) {
                items(events.takeLast(10).reversed()) { event ->
                    EventRow(event)
                    HorizontalDivider(color = MaterialTheme.colorScheme.outline.copy(alpha = 0.08f))
                }
            }
        }

        Spacer(Modifier.height(16.dp))

        // ── Alerts ───────────────────────────────────────────────────
        if (alerts.isNotEmpty()) {
            SectionTitle("🔔 Cảnh báo", modifier = Modifier.padding(horizontal = 16.dp))
            Spacer(Modifier.height(8.dp))
            alerts.take(3).forEach { alert ->
                AlertCard(alert = alert, onAck = { vm.acknowledgeAlert(alert.id) })
                Spacer(Modifier.height(8.dp))
            }
        }

        Spacer(Modifier.height(80.dp))
    }
}

// ─────────────────────────────────────────────────────────────────────────
//  Top Bar
// ─────────────────────────────────────────────────────────────────────────

@Composable
private fun TopBarSection(isRunning: Boolean, onToggle: () -> Unit) {
    Surface(
        color     = MaterialTheme.colorScheme.surface,
        tonalElevation = 2.dp
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(Modifier.weight(1f)) {
                Text(
                    "Wifi-Censor",
                    style     = MaterialTheme.typography.titleLarge,
                    fontWeight= FontWeight.ExtraBold,
                    color     = MaterialTheme.colorScheme.primary
                )
                Text(
                    if (isRunning) "🟢 Đang giám sát" else "⚪ Đã dừng",
                    style = MaterialTheme.typography.bodySmall,
                    color = if (isRunning) Color(0xFF10B981) else MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            FilledTonalButton(onClick = onToggle) {
                Icon(
                    if (isRunning) Icons.Default.Stop else Icons.Default.PlayArrow,
                    contentDescription = null,
                    modifier = Modifier.size(18.dp)
                )
                Spacer(Modifier.width(6.dp))
                Text(if (isRunning) "Dừng" else "Bắt đầu")
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────
//  Status Hero Card
// ─────────────────────────────────────────────────────────────────────────

@Composable
private fun StatusHeroCard(
    result:   PresenceEngine.PresenceResult?,
    modifier: Modifier = Modifier
) {
    val presence  = result?.presence  ?: PresenceEngine.PresenceState.UNKNOWN
    val activity  = result?.activity  ?: PresenceEngine.ActivityState.UNKNOWN
    val confidence= result?.confidence ?: 0f

    val containerColor = when (presence) {
        PresenceEngine.PresenceState.PRESENT -> Color(0xFF10B981)
        PresenceEngine.PresenceState.ABSENT  -> Color(0xFF6B7280)
        PresenceEngine.PresenceState.UNKNOWN -> Color(0xFF6366F1)
    }

    val pulseAnim = rememberInfiniteTransition(label = "pulse")
    val pulseScale by pulseAnim.animateFloat(
        initialValue = 0.95f, targetValue = 1.05f,
        animationSpec = infiniteRepeatable(tween(1500), RepeatMode.Reverse),
        label = "scale"
    )

    Card(
        modifier = modifier.fillMaxWidth(),
        colors   = CardDefaults.cardColors(
            containerColor = containerColor.copy(alpha = 0.1f)
        ),
        border   = BorderStroke(1.5.dp, containerColor.copy(alpha = 0.4f)),
        shape    = RoundedCornerShape(20.dp)
    ) {
        Row(
            modifier = Modifier.padding(20.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Animated beacon
            Box(
                modifier          = Modifier.size(80.dp),
                contentAlignment  = Alignment.Center
            ) {
                if (presence == PresenceEngine.PresenceState.PRESENT) {
                    Box(
                        modifier = Modifier
                            .size(80.dp)
                            .scale(pulseScale)
                            .background(containerColor.copy(alpha = 0.15f), CircleShape)
                    )
                }
                Box(
                    modifier         = Modifier
                        .size(58.dp)
                        .background(containerColor.copy(alpha = 0.2f), CircleShape)
                        .border(2.dp, containerColor.copy(alpha = 0.5f), CircleShape),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text  = when (presence) {
                            PresenceEngine.PresenceState.PRESENT -> "👤"
                            PresenceEngine.PresenceState.ABSENT  -> "🏠"
                            PresenceEngine.PresenceState.UNKNOWN -> "📡"
                        },
                        fontSize = 28.sp
                    )
                }
            }

            Spacer(Modifier.width(20.dp))

            Column(Modifier.weight(1f)) {
                Text(
                    text = when (presence) {
                        PresenceEngine.PresenceState.PRESENT -> "Có người trong phòng"
                        PresenceEngine.PresenceState.ABSENT  -> "Vắng phòng"
                        PresenceEngine.PresenceState.UNKNOWN -> "Đang phân tích..."
                    },
                    style      = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color      = containerColor
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = when (activity) {
                        PresenceEngine.ActivityState.WALKING    -> "🚶 Đang di chuyển"
                        PresenceEngine.ActivityState.STATIONARY -> "🪑 Đang ngồi / nghỉ"
                        PresenceEngine.ActivityState.SLEEPING   -> "😴 Có thể đang ngủ"
                        PresenceEngine.ActivityState.MOVING     -> "🏃 Đang hoạt động"
                        else                                     -> "Đang quan sát..."
                    },
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(Modifier.height(10.dp))
                // Confidence bar
                Text(
                    "Độ tin cậy: ${(confidence * 100).toInt()}%",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(Modifier.height(4.dp))
                LinearProgressIndicator(
                    progress  = { confidence },
                    modifier  = Modifier.fillMaxWidth().height(6.dp).clip(RoundedCornerShape(3.dp)),
                    color     = containerColor,
                    trackColor= containerColor.copy(alpha = 0.15f)
                )
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────
//  Stats Row
// ─────────────────────────────────────────────────────────────────────────

@Composable
private fun StatsRow(
    presentMin:   Long,
    absentMin:    Long,
    rssiVariance: Float,
    modifier:     Modifier = Modifier
) {
    Row(modifier = modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        StatChip("$presentMin", "phút",   "Có mặt",    Color(0xFF10B981), Modifier.weight(1f))
        StatChip("$absentMin",  "phút",   "Vắng phòng",Color(0xFF6B7280), Modifier.weight(1f))
        StatChip("%.1f".format(rssiVariance), "var", "Nhiễu",     Color(0xFF6366F1), Modifier.weight(1f))
    }
}

@Composable
private fun StatChip(value: String, unit: String, label: String, color: Color, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier,
        colors   = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.08f)),
        border   = BorderStroke(1.dp, color.copy(alpha = 0.25f)),
        shape    = RoundedCornerShape(14.dp)
    ) {
        Column(
            modifier          = Modifier.padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(value, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, color = color)
            Text(unit,  style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(label, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant, textAlign = TextAlign.Center)
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────
//  Event Row
// ─────────────────────────────────────────────────────────────────────────

@Composable
private fun EventRow(event: com.example.wificensor.data.PresenceEvent) {
    val fmt   = SimpleDateFormat("HH:mm", Locale.getDefault())
    val color = when (event.eventType) {
        "PRESENT" -> Color(0xFF10B981)
        "ABSENT"  -> Color(0xFF6B7280)
        else      -> Color(0xFFF59E0B)
    }
    Row(
        modifier          = Modifier.fillMaxWidth().padding(vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(10.dp)
                .background(color, CircleShape)
        )
        Spacer(Modifier.width(12.dp))
        Text(
            fmt.format(Date(event.startTime)),
            style    = MaterialTheme.typography.labelMedium,
            color    = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.width(44.dp)
        )
        Column(Modifier.weight(1f)) {
            Text(
                when (event.eventType) {
                    "PRESENT" -> "Phát hiện có người"
                    "ABSENT"  -> "Ra khỏi phòng"
                    else      -> event.eventType
                },
                style      = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Medium
            )
            if (event.activity.isNotBlank()) {
                Text(
                    event.activity.lowercase().replaceFirstChar { it.uppercase() },
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────
//  Alert Card
// ─────────────────────────────────────────────────────────────────────────

@Composable
private fun AlertCard(
    alert: com.example.wificensor.data.AlertEvent,
    onAck: () -> Unit
) {
    val color = if (alert.level == "DANGER") Color(0xFFEF4444) else Color(0xFFF59E0B)
    Card(
        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp),
        colors   = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.08f)),
        border   = BorderStroke(1.dp, color.copy(alpha = 0.35f)),
        shape    = RoundedCornerShape(14.dp)
    ) {
        Row(
            modifier          = Modifier.padding(14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(if (alert.level == "DANGER") "🔴" else "🟡", fontSize = 22.sp)
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(alert.title,   style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold, color = color)
                Text(alert.message, style = MaterialTheme.typography.bodySmall,  color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            if (!alert.acknowledged) {
                TextButton(onClick = onAck) { Text("OK", color = color) }
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────
//  Helpers
// ─────────────────────────────────────────────────────────────────────────

@Composable
fun SectionTitle(text: String, modifier: Modifier = Modifier) {
    Text(
        text,
        style      = MaterialTheme.typography.titleSmall,
        fontWeight = FontWeight.SemiBold,
        modifier   = modifier
    )
}

@Composable
fun EmptyStateCard(text: String, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier.fillMaxWidth(),
        colors   = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(0.4f)),
        shape    = RoundedCornerShape(14.dp)
    ) {
        Box(Modifier.fillMaxWidth().padding(24.dp), Alignment.Center) {
            Text(text, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant, textAlign = TextAlign.Center)
        }
    }
}
