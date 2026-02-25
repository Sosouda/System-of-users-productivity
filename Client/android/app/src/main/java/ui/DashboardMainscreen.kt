package ui

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ExitToApp
import androidx.compose.material.icons.filled.Sync
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import api.AuthManager
import api.SyncState
import data.TaskDao
import kotlinx.coroutines.launch
import ml.TaskLoad.DashboardViewModel
import ml.TaskLoad.DashboardViewModelFactory
import java.time.OffsetDateTime


@Composable
fun DrawDashboard() {
    val context = LocalContext.current
    val app = context.applicationContext as App
    val dao = app.database.taskDao()
    val viewModel: DashboardViewModel = viewModel(
        factory = DashboardViewModelFactory(dao, context)
    )

    val scrollState = rememberScrollState()

    LaunchedEffect(Unit) {
        viewModel.refreshCapacity()
    }

    val currentLoad = viewModel.capacityPercentage

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(BackgroundColor)
            .verticalScroll(scrollState)
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(20.dp)
    ) {
        Text(
            text = "Панель отслеживания",
            style = TextStyle(fontSize = 24.sp, fontWeight = FontWeight.Bold, color = TextDark),
            modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)
        )

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(
                modifier = Modifier.weight(1f),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                RefreshData()
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Синхронизировать",
                    style = TextStyle(fontSize = 14.sp, color = TextDark)
                )
            }

            Column(
                modifier = Modifier.weight(1f),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                IconButton(
                    onClick = {
                        AuthManager.handleLogout(context)
                    },
                    modifier = Modifier
                        .size(48.dp)
                        .background(Color.White, shape = CircleShape)
                        .shadow(2.dp, CircleShape)
                ) {
                    Icon(
                        imageVector = Icons.Default.ExitToApp,
                        contentDescription = "Logout",
                        tint = Color(0xFFD32F2F)
                    )
                }
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Выйти из аккаунта",
                    style = TextStyle(fontSize = 14.sp, color = TextDark)
                )
            }
        }

        DashboardCard(title = "Загруженность") {
            Box(modifier = Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                UserLoadPieChart(currentLoad)
            }
        }

        DashboardCard(title = "Задачи дедлайн которых наступит скоро") {
            Draw3Tasks(dao)
        }

        DashboardCard(title = "Тренд выполнения задач") {
            DrawGraphs(dao)
        }

        Spacer(modifier = Modifier.height(20.dp))
    }
}

@Composable
fun RefreshData() {
    var syncStatus by remember { mutableStateOf<SyncState>(SyncState.Idle) }
    val scope = rememberCoroutineScope()
    val context = LocalContext.current

    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Center,
            modifier = Modifier.fillMaxWidth()
        ) {
            IconButton(
                onClick = {
                    scope.launch {
                        syncStatus = SyncState.Loading
                        val (success, message) = api.SyncManager.runSync(context)

                        syncStatus = if (success) {
                            SyncState.Success(message)
                        } else {
                            SyncState.Error(message)
                        }
                    }
                },
                enabled = syncStatus !is SyncState.Loading
            ) {
                if (syncStatus is SyncState.Loading) {
                    CircularProgressIndicator(modifier = Modifier.size(24.dp), strokeWidth = 2.dp)
                } else {
                    Icon(
                        imageVector = Icons.Default.Sync,
                        contentDescription = "Sync",
                        tint = if (syncStatus is SyncState.Error) Color.Red else MaterialTheme.colorScheme.primary
                    )
                }
            }

            when (val state = syncStatus) {
                is SyncState.Success -> {
                    Text(state.message, color = Color.Gray, fontSize = 12.sp, modifier = Modifier.padding(start = 8.dp))
                    LaunchedEffect(state) {
                        kotlinx.coroutines.delay(3000)
                        syncStatus = SyncState.Idle
                    }
                }
                is SyncState.Error -> {
                    Text("Fail: ${state.error}", color = Color.Red, fontSize = 12.sp, modifier = Modifier.padding(start = 8.dp))
                }
                else -> {}
            }
        }
    }
}
@Composable
fun DashboardCard(title: String, content: @Composable () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(SurfaceColor, shape = RoundedCornerShape(16.dp))
            .padding(16.dp)
    ) {
        Text(
            text = title,
            style = TextStyle(fontSize = 16.sp, fontWeight = FontWeight.Bold, color = TextGray),
            modifier = Modifier.padding(bottom = 12.dp)
        )
        content()
    }
}

@Composable
fun Draw3Tasks(dao: TaskDao) {
    val now = remember { OffsetDateTime.now() }

    val tasks by dao.selectClosestTasks(now).collectAsState(initial = emptyList())

    if (tasks.isEmpty()) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 16.dp),
            contentAlignment = Alignment.Center
        ) {
            Text("Нет задач в работе", color = TextGray, fontSize = 16.sp)
        }
    } else {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            tasks.forEach { task ->
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(BackgroundColor, RoundedCornerShape(12.dp))
                        .padding(12.dp)
                ) {
                    Text(
                        text = task.title,
                        fontWeight = FontWeight.Bold,
                        color = TextDark,
                        maxLines = 1
                    )
                    Text(
                        text = task.description ?: "",
                        color = TextGray,
                        fontSize = 14.sp,
                        maxLines = 2
                    )
                }
            }
        }
    }
}
@Composable
fun UserLoadPieChart(percentage: Int) {
    val animatedPercentage by animateFloatAsState(
        targetValue = percentage.toFloat(),
        animationSpec = tween(durationMillis = 1200)
    )

    Box(contentAlignment = Alignment.Center, modifier = Modifier.size(200.dp)) {
        Canvas(modifier = Modifier.fillMaxSize().padding(16.dp)) {
            val strokeWidth = 30f

            drawCircle(
                color = Color(0xFFF0F2F5),
                style = Stroke(width = strokeWidth)
            )

            drawArc(
                color = PrimaryBlue,
                startAngle = -90f,
                sweepAngle = (animatedPercentage / 100f) * 360f,
                useCenter = false,
                style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
            )
        }

        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(
                text = "${percentage}%",
                style = TextStyle(fontSize = 36.sp, fontWeight = FontWeight.ExtraBold, color = TextDark)
            )
            Text(text = "Load", color = TextGray, fontSize = 14.sp)
        }
    }
}

@Composable
fun TasksInProgressPlot(dates: List<String>, values: List<Float>) {
    if (values.isEmpty()) return

    val maxValue = (values.maxOrNull() ?: 0f).let { if (it < 5f) 5f else it }

    val textPaint = remember {
        android.graphics.Paint().apply {
            color = android.graphics.Color.GRAY
            textSize = 28f
            textAlign = android.graphics.Paint.Align.RIGHT
            isAntiAlias = true
        }
    }

    Canvas(
        modifier = Modifier
            .fillMaxWidth()
            .height(220.dp)
            .padding(top = 16.dp, end = 20.dp, bottom = 8.dp)
    ) {
        val leftPadding = 70f
        val bottomPadding = 60f

        val chartWidth = size.width - leftPadding
        val chartHeight = size.height - bottomPadding

        val spacingX = if (dates.size > 1) chartWidth / (dates.size - 1) else chartWidth

        val ySteps = 4
        for (i in 0..ySteps) {
            val yValue = (maxValue / ySteps) * i
            val yPos = chartHeight - (yValue / maxValue * chartHeight)

            drawLine(
                color = Color.Gray.copy(alpha = 0.2f),
                start = Offset(leftPadding, yPos),
                end = Offset(size.width, yPos),
                strokeWidth = 1f
            )

            drawContext.canvas.nativeCanvas.drawText(
                yValue.toInt().toString(),
                leftPadding - 15f,
                yPos + 10f,
                textPaint
            )
        }

        val linePath = Path()
        val fillPath = Path()

        values.forEachIndexed { index, value ->
            val x = leftPadding + (index * spacingX)
            val y = chartHeight - (value / maxValue * chartHeight)

            if (index == 0) {
                linePath.moveTo(x, y)
                fillPath.moveTo(x, chartHeight)
                fillPath.lineTo(x, y)
            } else {
                linePath.lineTo(x, y)
                fillPath.lineTo(x, y)
            }

            if (index == values.lastIndex) {
                fillPath.lineTo(x, chartHeight)
                fillPath.close()
            }
        }

        drawPath(
            path = fillPath,
            color = PrimaryBlue.copy(alpha = 0.15f)
        )

        drawPath(
            path = linePath,
            color = PrimaryBlue,
            style = Stroke(width = 8f, cap = StrokeCap.Round, join = StrokeJoin.Round)
        )

        values.forEachIndexed { index, value ->
            val x = leftPadding + (index * spacingX)
            val y = chartHeight - (value / maxValue * chartHeight)

            drawCircle(color = PrimaryBlue, radius = 6f, center = Offset(x, y))
            drawCircle(color = Color.White, radius = 3f, center = Offset(x, y))

            drawContext.canvas.nativeCanvas.drawText(
                dates[index],
                x,
                size.height - 5f,
                android.graphics.Paint().apply {
                    color = android.graphics.Color.GRAY
                    textSize = 26f
                    textAlign = android.graphics.Paint.Align.CENTER
                }
            )
        }
    }
}
@Composable
fun DrawGraphs(dao: TaskDao) {
    val statsList by dao.selectLastWeekStats().collectAsState(initial = emptyList())

    if (statsList.isEmpty()) {
        Box(modifier = Modifier.fillMaxWidth().height(100.dp), contentAlignment = Alignment.Center) {
            Text("No activity data yet", color = TextGray)
        }
    } else {
        val sortedStats = statsList.sortedBy { it.date }

        val chartLabels = sortedStats.map { it.date.dayOfMonth.toString() + "." + it.date.monthValue }
        val chartValues = sortedStats.map { it.completedTasks.toFloat() }

        TasksInProgressPlot(dates = chartLabels, values = chartValues)
    }
}