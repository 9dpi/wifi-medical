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

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material.icons.filled.List
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.wificensor.data.PresenceEvent
import java.text.SimpleDateFormat
import java.util.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HistoryScreen(
    events: List<PresenceEvent>,
    modifier: Modifier = Modifier
) {
    var selectedFilter by remember { mutableStateOf("ALL") } // ALL, PRESENT, ALERT/ANOMALY

    val filteredEvents = remember(events, selectedFilter) {
        when (selectedFilter) {
            "PRESENT" -> events.filter { it.eventType == "PRESENT" }
            "ALERT" -> events.filter { it.eventType == "FALL_SUSPECTED" || it.eventType == "ANOMALY" }
            else -> events
        }
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
    ) {
        // --- Header Section ---
        Surface(
            color = MaterialTheme.colorScheme.surface,
            tonalElevation = 2.dp
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp)
            ) {
                Text(
                    "Lịch sử hoạt động",
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.ExtraBold,
                    color = MaterialTheme.colorScheme.primary
                )
                Text(
                    "Theo dõi nhật ký hoạt động thu thập qua Wi-Fi",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // --- Filter Pills ---
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            FilterChip(
                selected = selectedFilter == "ALL",
                onClick = { selectedFilter = "ALL" },
                label = { Text("Tất cả") },
                leadingIcon = { Icon(Icons.Default.List, null, modifier = Modifier.size(16.dp)) }
            )
            FilterChip(
                selected = selectedFilter == "PRESENT",
                onClick = { selectedFilter = "PRESENT" },
                label = { Text("Có mặt") },
                leadingIcon = { Text("👤", fontSize = 12.sp) }
            )
            FilterChip(
                selected = selectedFilter == "ALERT",
                onClick = { selectedFilter = "ALERT" },
                label = { Text("Cảnh báo") },
                leadingIcon = { Icon(Icons.Default.Warning, null, modifier = Modifier.size(16.dp)) }
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        // --- Summary Stats Card ---
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f)),
            shape = RoundedCornerShape(16.dp)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                horizontalArrangement = Arrangement.SpaceAround
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        "${events.size}",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                    Text("Tổng sự kiện", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    val activeEvents = events.filter { it.activity == "WALKING" || it.activity == "MOVING" }.size
                    Text(
                        "$activeEvents",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF10B981)
                    )
                    Text("Di chuyển", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    val alerts = events.filter { it.eventType == "FALL_SUSPECTED" || it.eventType == "ANOMALY" }.size
                    Text(
                        "$alerts",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFFEF4444)
                    )
                    Text("Cảnh báo", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // --- Timeline List ---
        if (filteredEvents.isEmpty()) {
            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("📭", fontSize = 48.sp)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        "Không tìm thấy sự kiện nào tương ứng.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        textAlign = TextAlign.Center
                    )
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(filteredEvents) { event ->
                    HistoryEventCard(event)
                }
            }
        }
    }
}

@Composable
fun HistoryEventCard(event: PresenceEvent) {
    val timeFmt = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
    val dateFmt = SimpleDateFormat("dd/MM/yyyy", Locale.getDefault())
    
    val dateStr = dateFmt.format(Date(event.startTime))
    val timeStr = timeFmt.format(Date(event.startTime))
    
    val durationText = if (event.endTime != null) {
        val diffMs = event.endTime - event.startTime
        val diffMin = diffMs / 60000
        val diffSec = (diffMs % 60000) / 1000
        if (diffMin > 0) "${diffMin}p ${diffSec}s" else "${diffSec}s"
    } else {
        "Đang tiếp diễn"
    }

    val typeColor = when (event.eventType) {
        "PRESENT" -> Color(0xFF10B981)
        "ABSENT" -> Color(0xFF6B7280)
        "FALL_SUSPECTED" -> Color(0xFFEF4444)
        else -> Color(0xFFF59E0B)
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Event status indicator circle
            Box(
                modifier = Modifier
                    .size(16.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(typeColor.copy(alpha = 0.2f))
                    .border(2.dp, typeColor, RoundedCornerShape(8.dp))
            )

            Spacer(modifier = Modifier.width(16.dp))

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = when (event.eventType) {
                        "PRESENT" -> "Phát hiện có người"
                        "ABSENT" -> "Vắng phòng / Không phát hiện"
                        "FALL_SUSPECTED" -> "⚠️ Cảnh báo té ngã!"
                        else -> event.eventType
                    },
                    fontWeight = FontWeight.Bold,
                    style = MaterialTheme.typography.bodyLarge,
                    color = if (event.eventType == "FALL_SUSPECTED") typeColor else MaterialTheme.colorScheme.onSurface
                )
                
                Spacer(modifier = Modifier.height(2.dp))
                
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    if (event.activity.isNotBlank()) {
                        Text(
                            text = "Trạng thái: " + when (event.activity) {
                                "WALKING" -> "🚶 Di chuyển"
                                "STATIONARY" -> "🪑 Đứng/Ngồi im"
                                "SLEEPING" -> "😴 Có thể đang ngủ"
                                "MOVING" -> "🏃 Hoạt động mạnh"
                                else -> event.activity
                            },
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                    Text(
                        text = "• Thời lượng: $durationText",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            Column(horizontalAlignment = Alignment.End) {
                Text(
                    text = timeStr,
                    fontWeight = FontWeight.Bold,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Text(
                    text = dateStr,
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}
