package io.eidos.zerolayer.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.clickable
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import kotlinx.coroutines.delay
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.data.GameLog
import io.eidos.zerolayer.ui.theme.EidosCyan
import io.eidos.zerolayer.ui.theme.EidosGlass
import io.eidos.zerolayer.ui.theme.EidosNeon
import io.eidos.zerolayer.ui.theme.EidosRed
import java.text.SimpleDateFormat
import java.util.*

@Composable
fun TerminalLog(logs: List<GameLog>) {
    val listState = rememberLazyListState()
    val dateFormat = SimpleDateFormat("HH:mm:ss", Locale.getDefault())

    LaunchedEffect(logs.size) {
        if (logs.isNotEmpty() && listState.firstVisibleItemIndex <= 1) {
            listState.animateScrollToItem(0)
        }
    }

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .height(150.dp)
            .background(EidosGlass)
            .padding(8.dp)
    ) {
        Text(
            "TERMINAL // LOGS",
            color = EidosCyan,
            fontSize = 10.sp,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(bottom = 4.dp)
        )
        
        LazyColumn(
            state = listState,
            modifier = Modifier.fillMaxSize()
        ) {
            itemsIndexed(logs) { index, log ->
                if (index == 0) {
                    TypingLogItem(log, dateFormat)
                } else {
                    StaticLogItem(log, dateFormat)
                }
            }
        }
    }
}

@Composable
fun TypingLogItem(log: GameLog, dateFormat: SimpleDateFormat) {
    var displayedText by remember(log.id) { mutableStateOf("") }
    var isSkipped by remember(log.id) { mutableStateOf(false) }
    
    val speed = if (log.type == "combat") 10L else 30L

    LaunchedEffect(log.id, isSkipped) {
        if (isSkipped) {
            displayedText = log.message
        } else {
            displayedText = ""
            log.message.forEach { char ->
                displayedText += char
                delay(speed)
            }
        }
    }

    LogItemRow(
        timestamp = dateFormat.format(Date(log.timestamp)),
        message = displayedText,
        type = log.type,
        modifier = Modifier.clickable { isSkipped = true }
    )
}

@Composable
fun StaticLogItem(log: GameLog, dateFormat: SimpleDateFormat) {
    LogItemRow(
        timestamp = dateFormat.format(Date(log.timestamp)),
        message = log.message,
        type = log.type
    )
}

@Composable
fun LogItemRow(timestamp: String, message: String, type: String, modifier: Modifier = Modifier) {
    Row(modifier = modifier.padding(vertical = 2.dp)) {
        Text(
            "[$timestamp] ",
            color = Color.Gray,
            fontSize = 10.sp
        )
        Text(
            message,
            color = when (type) {
                "combat" -> EidosRed
                "loot" -> EidosNeon
                "error" -> EidosRed
                else -> Color.White
            },
            fontSize = 11.sp,
            lineHeight = 14.sp
        )
    }
}
