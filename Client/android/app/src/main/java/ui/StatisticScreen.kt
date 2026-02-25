package ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import data.TaskDao
import kotlinx.coroutines.launch

val priorityTranslationsStat = mapOf(
    "Casual" to "Обычный",
    "Low" to "Низкий",
    "Mid" to "Средний",
    "High" to "Высокий",
    "Extreme" to "Критический"
)

val statusTranslationsStat = mapOf(
    "underway" to "В работе",
    "completed" to "Выполнено",
    "overdue" to "Просрочено"
)

val taskTypeTranslationsStat = mapOf(
    "Dust Cleaning" to "Уборка",
    "Meeting" to "Встречи",
    "Documentation" to "Документы",
    "Customer Support" to "Поддержка",
    "Code Bug Fix" to "Баги",
    "Research" to "Исследования",
    "Feature Development" to "Разработка",
    "Optimization" to "Оптимизация",
    "Deployment" to "Деплой",
    "Project Management" to "Менеджмент",
    "Other" to "Прочее"
)

@Composable
fun DrawStatisticScreen(dao: TaskDao) {
    var selectedChart by remember { mutableStateOf(0) }
    var chartLabels by remember { mutableStateOf<List<String>>(emptyList()) }
    var chartValues by remember { mutableStateOf<List<Float>>(emptyList()) }
    val scope = rememberCoroutineScope()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(BackgroundColor)
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "Аналитика",
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(bottom = 16.dp)
        )

        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                StatButton("Приоритеты", Modifier.weight(1f)) {
                    selectedChart = 1
                    scope.launch {
                        val res = dao.selectPriorityCounts()
                        chartLabels = res.map { priorityTranslationsStat[it.label] ?: it.label }
                        chartValues = res.map { it.value }
                    }
                }
                StatButton("Статусы", Modifier.weight(1f)) {
                    selectedChart = 2
                    scope.launch {
                        val res = dao.selectAllTasks()
                        chartLabels = res.map { statusTranslationsStat[it.label] ?: it.label }
                        chartValues = res.map { it.value }
                    }
                }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                StatButton("Категории (Все)", Modifier.weight(1f)) {
                    selectedChart = 3
                    scope.launch {
                        val res = dao.selectTasksByType()
                        chartLabels = res.map { taskTypeTranslationsStat[it.label] ?: it.label }
                        chartValues = res.map { it.value }
                    }
                }
                StatButton("Категории (Вып.)", Modifier.weight(1f)) {
                    selectedChart = 4
                    scope.launch {
                        val res = dao.selectCompletedByTypes()
                        chartLabels = res.map { taskTypeTranslationsStat[it.label] ?: it.label }
                        chartValues = res.map { it.value }
                    }
                }
            }

            StatButton("Динамика нагрузки", Modifier.fillMaxWidth()) {
                selectedChart = 5
                scope.launch {
                    val currentUnderway = dao.countUnderwayTasks()
                    val today = java.time.LocalDate.now()
                    val existingStats = dao.findDailyStats(today)
                    val updatedStats = existingStats?.copy(inProgressTasks = currentUnderway)
                        ?: data.DailyStatsEntity(
                            date = today,
                            inProgressTasks = currentUnderway,
                            completedTasks = 0,
                            totalTasks = 0,
                            overdueTasks = 0
                        )

                    dao.upsertDailyStats(updatedStats)
                    val res = dao.selectDailyStatsForTrend().reversed()

                    chartLabels = res.map { it.date.toString().takeLast(5) }
                    chartValues = res.map { it.inProgressTasks.toFloat() }
                }
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        Surface(
            modifier = Modifier.fillMaxSize(),
            shape = RoundedCornerShape(16.dp),
            color = SurfaceColor,
            tonalElevation = 2.dp
        ) {
            if (selectedChart == 0) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text("Выберите раздел для анализа", color = TextGray)
                }
            } else {
                Column(Modifier.padding(16.dp)) {
                    val title = when(selectedChart) {
                        1 -> "Распределение по приоритетам"
                        2 -> "Статусы всех задач"
                        3 -> "Все задачи по категориям"
                        4 -> "Выполненные по категориям"
                        else -> "Задачи в работе (динамика за 10 дней)"
                    }
                    Text(title, fontWeight = FontWeight.Bold, color = TextDark, modifier = Modifier.padding(bottom = 16.dp))

                    if (selectedChart in 1..4) {
                        BarChartPro(chartLabels, chartValues)
                    } else {
                        LineChartPro(chartLabels, chartValues)
                    }
                }
            }
        }
    }
}

@Composable
fun StatButton(text: String, modifier: Modifier, onClick: () -> Unit) {
    Button(
        onClick = onClick,
        modifier = modifier.height(50.dp),
        shape = RoundedCornerShape(12.dp),
        colors = ButtonDefaults.buttonColors(containerColor = PrimaryBlue)
    ) {
        Text(text, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
fun BarChartPro(labels: List<String>, values: List<Float>) {
    Canvas(modifier = Modifier.fillMaxSize().padding(bottom = 60.dp, start = 30.dp, end = 10.dp, top = 20.dp)) {
        val maxValue = (values.maxOrNull() ?: 1f).coerceAtLeast(1f)
        val spaceX = size.width / labels.size
        val barWidth = spaceX * 0.6f

        val steps = 5
        for (i in 0..steps) {
            val y = size.height - (i * size.height / steps)
            drawLine(GridColor, Offset(0f, y), Offset(size.width, y), 1f)
            drawContext.canvas.nativeCanvas.drawText(
                (maxValue * i / steps).toInt().toString(),
                -25f, y + 10f,
                android.graphics.Paint().apply { textSize = 28f; color = android.graphics.Color.GRAY }
            )
        }

        values.forEachIndexed { index, value ->
            val barHeight = (value / maxValue) * size.height
            val x = index * spaceX + (spaceX - barWidth) / 2
            val y = size.height - barHeight

            drawRect(
                color = PrimaryBlue,
                topLeft = Offset(x, y),
                size = androidx.compose.ui.geometry.Size(barWidth, barHeight)
            )

            drawContext.canvas.nativeCanvas.apply {
                save()
                rotate(45f, x + barWidth / 2, size.height + 25f)
                drawText(
                    labels[index],
                    x + barWidth / 2, size.height + 25f,
                    android.graphics.Paint().apply {
                        textSize = 26f
                        textAlign = android.graphics.Paint.Align.LEFT
                        color = android.graphics.Color.BLACK
                        isFakeBoldText = true
                    }
                )
                restore()
            }
        }
    }
}

@Composable
fun LineChartPro(labels: List<String>, values: List<Float>) {
    if (labels.isEmpty() || values.isEmpty()) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Text("Нет данных для отображения", color = Color.Gray)
        }
        return
    }

    Canvas(modifier = Modifier
        .fillMaxSize()
        .padding(bottom = 60.dp, start = 40.dp, end = 20.dp, top = 20.dp)
    ) {
        val maxValue = (values.maxOrNull() ?: 1f).coerceAtLeast(1f)
        val stepsY = 5
        val spaceX = if (labels.size > 1) size.width / (labels.size - 1) else size.width

        val paintY = android.graphics.Paint().apply {
            textSize = 28f
            color = android.graphics.Color.GRAY
            textAlign = android.graphics.Paint.Align.RIGHT
        }

        for (i in 0..stepsY) {
            val y = size.height - (i * size.height / stepsY)
            drawLine(
                color = GridColor.copy(alpha = 0.5f),
                start = Offset(0f, y),
                end = Offset(size.width, y),
                strokeWidth = 1f
            )
            val yLabel = (maxValue * i / stepsY).toInt().toString()
            drawContext.canvas.nativeCanvas.drawText(yLabel, -15f, y + 10f, paintY)
        }

        if (values.size > 1) {
            val path = Path().apply {
                values.forEachIndexed { index, value ->
                    val x = index * spaceX
                    val y = size.height - (value / maxValue * size.height)
                    if (index == 0) moveTo(x, y) else lineTo(x, y)
                }
            }
            drawPath(
                path = path,
                color = PrimaryBlue,
                style = Stroke(width = 8f, cap = StrokeCap.Round)
            )
        }

        val paintX = android.graphics.Paint().apply {
            textSize = 26f
            color = android.graphics.Color.BLACK
            textAlign = android.graphics.Paint.Align.CENTER
        }

        values.forEachIndexed { index, value ->
            val x = index * spaceX
            val y = size.height - (value / maxValue * size.height)

            drawCircle(color = PrimaryBlue, radius = 10f, center = Offset(x, y))
            drawCircle(color = Color.White, radius = 5f, center = Offset(x, y))

            if (index < labels.size) {
                drawContext.canvas.nativeCanvas.drawText(labels[index], x, size.height + 45f, paintX)
            }
        }
    }
}