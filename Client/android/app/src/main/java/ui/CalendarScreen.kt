package ui

import android.widget.Toast
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import data.DailyStatsEntity
import data.TaskDao
import data.TaskEntity
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import ml.TaskPriority.TaskPriorityPredictor
import java.time.*
import java.util.UUID
import kotlin.math.max
import kotlin.math.min


val taskTypeMap = mapOf(
    "Dust Cleaning" to "Уборка",
    "Meeting" to "Встреча",
    "Documentation" to "Документация",
    "Customer Support" to "Поддержка",
    "Code Bug Fix" to "Исправление багов",
    "Research" to "Исследование",
    "Feature Development" to "Разработка",
    "Optimization" to "Оптимизация",
    "Deployment" to "Деплой",
    "Project Management" to "Менеджмент",
    "Other" to "Другое"
)

val priorityMap = mapOf(
    "Casual" to "Повседневный",
    "Low" to "Низкий",
    "Mid" to "Средний",
    "High" to "Высокий",
    "Extreme" to "Критический"
)

fun levenshteinDistance(s1: String, s2: String): Int {
    val dp = IntArray(s2.length + 1) { it }
    for (i in 1..s1.length) {
        var prev = dp[0]
        dp[0] = i
        for (j in 1..s2.length) {
            val temp = dp[j]
            dp[j] = if (s1[i - 1] == s2[j - 1]) prev else 1 + minOf(prev, minOf(dp[j - 1], dp[j]))
            prev = temp
        }
    }
    return dp[s2.length]
}

fun calculateSimilarity(s1: String, s2: String): Double {
    val str1 = s1.lowercase().trim()
    val str2 = s2.lowercase().trim()
    val longer = if (str1.length > str2.length) str1 else str2
    val shorter = if (str1.length > str2.length) str2 else str1
    if (longer.isEmpty()) return 1.0
    val distance = levenshteinDistance(longer, shorter)
    return (longer.length - distance) / longer.length.toDouble()
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DrawCalendar() {
    val datePickerState = rememberDatePickerState(initialSelectedDateMillis = System.currentTimeMillis())
    var showCreateTask by remember { mutableStateOf(false) }

    val selectedDate: LocalDate = datePickerState.selectedDateMillis?.let { millis ->
        Instant.ofEpochMilli(millis).atZone(ZoneId.systemDefault()).toLocalDate()
    } ?: LocalDate.now()

    Scaffold(
        containerColor = BackgroundColor,
        floatingActionButton = {
            FloatingActionButton(
                onClick = { showCreateTask = true },
                containerColor = PrimaryBlue,
                contentColor = Color.White,
                shape = RoundedCornerShape(16.dp)
            ) {
                Icon(Icons.Default.Add, contentDescription = "Добавить задачу")
            }
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Text(
                text = "План задач",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = TextDark
            )

            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(24.dp),
                color = SurfaceColor,
                tonalElevation = 2.dp
            ) {
                DatePicker(
                    state = datePickerState,
                    showModeToggle = false, // Отключает текстовый ввод и упрощает выбор
                    title = null,
                    headline = null,
                    colors = DatePickerDefaults.colors(
                        selectedDayContainerColor = PrimaryBlue,
                        todayContentColor = PrimaryBlue,
                        todayDateBorderColor = PrimaryBlue
                    )
                )
            }

            Text(
                text = "Задачи на выбранную дату:",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold,
                color = TextDark
            )

            ListView(selectedDate)
        }
    }

    if (showCreateTask) {
        Dialog(onDismissRequest = { showCreateTask = false }) {
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .fillMaxHeight(0.9f),
                shape = RoundedCornerShape(28.dp),
                color = BackgroundColor
            ) {
                TaskCreation(
                    selectedDate = selectedDate,
                    onDismiss = { showCreateTask = false },
                    dao = (LocalContext.current.applicationContext as App).database.taskDao()
                )
            }
        }
    }
}

@Composable
fun ListView(selectedDate: LocalDate) {
    val context = LocalContext.current
    val dao = (context.applicationContext as App).database.taskDao()

    val dateRange = remember(selectedDate) {
        val start = selectedDate.atStartOfDay(ZoneOffset.UTC).toOffsetDateTime()
        val end = start.plusDays(1)
        Pair(start, end)
    }

    val tasks by dao.selectDailyTasks(dateRange.first, dateRange.second)
        .collectAsState(initial = emptyList())

    if (tasks.isEmpty()) {
        Text(
            text = "На этот день задач пока нет",
            modifier = Modifier.padding(16.dp),
            color = TextGray
        )
    } else {
        LazyColumn(Modifier.heightIn(max = 400.dp)) {
            items(tasks) { task ->
                TaskItem(task)
                Spacer(modifier = Modifier.height(8.dp))
            }
        }
    }
}

@Composable
fun TaskItem(task: TaskEntity) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        color = SurfaceColor,
        tonalElevation = 1.dp
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(text = task.title, fontWeight = FontWeight.Bold, color = TextDark)
                task.description?.let { Text(text = it, color = TextGray, fontSize = 14.sp) }
            }

            val rusPriority = priorityMap[task.finalPriority] ?: task.finalPriority

            Surface(
                color = when(task.finalPriority) {
                    "Extreme", "High" -> Color(0xFFFFE5E5)
                    "Mid" -> Color(0xFFFFF4E5)
                    else -> Color(0xFFE5F9E5)
                },
                shape = RoundedCornerShape(8.dp)
            ) {
                Text(
                    text = rusPriority,
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                    style = MaterialTheme.typography.labelSmall,
                    color = when(task.finalPriority) {
                        "Extreme", "High" -> Color(0xFFD32F2F)
                        "Mid" -> Color(0xFFF57C00)
                        else -> Color(0xFF388E3C)
                    },
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TaskCreation(
    selectedDate: LocalDate?,
    onDismiss: () -> Unit,
    dao: TaskDao
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    var title by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }
    var taskTypeRus by remember { mutableStateOf("") }
    var priorityRus by remember { mutableStateOf("Авто") }
    var selfPriority by remember { mutableStateOf(5f) }
    var influence by remember { mutableStateOf(5f) }

    var showDialog by remember { mutableStateOf(false) }
    var duplicateTaskInfo by remember { mutableStateOf("") }

    val scrollState = rememberScrollState()

    val performSave = suspend {
        val now = OffsetDateTime.now(ZoneOffset.UTC)
        val taskTypeEng = taskTypeMap.entries.find { it.value == taskTypeRus }?.key ?: "Other"
        val taskTypeId = dao.getTaskTypeIdByName(taskTypeEng) ?: 1
        val deadline = selectedDate?.atStartOfDay(ZoneOffset.UTC)?.toOffsetDateTime() ?: now.plusDays(1)

        val finalP = if (priorityRus == "Авто") {
            TaskPriorityPredictor(context).use {
                it.predict(
                    taskTypeEng,
                    calculateWorkingHours(LocalDateTime.now(), deadline.toLocalDateTime()),
                    selfPriority
                )
            }
        } else {
            priorityMap.entries.find { it.value == priorityRus }?.key ?: "Mid"
        }

        val task = TaskEntity(
            id = UUID.randomUUID().toString(),
            title = title,
            description = description,
            taskTypeId = taskTypeId,
            personalPriority = selfPriority.toInt(),
            influence = influence.toInt(),
            finalPriority = finalP,
            status = "underway",
            createdAt = now,
            updatedAt = now,
            deadline = deadline
        )

        dao.insertTask(task)
        updateDailyStats(dao, LocalDate.now())
        withContext(Dispatchers.Main) { onDismiss() }
    }

    // Основной контейнер диалога
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp)
    ) {
        Text(
            text = "Новая задача",
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
            color = TextDark,
            modifier = Modifier.padding(bottom = 16.dp)
        )

        Column(
            modifier = Modifier
                .weight(1f)
                .verticalScroll(scrollState),
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            OutlinedTextField(
                value = title,
                onValueChange = { title = it },
                label = { Text("Название") },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp)
            )

            OutlinedTextField(
                value = description,
                onValueChange = { description = it },
                label = { Text("Описание (необязательно)") },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                minLines = 3 // Чтобы сразу было видно область для текста
            )

            TaskDropdown("Категория", taskTypeRus, taskTypeMap.values.toList()) { taskTypeRus = it }
            TaskDropdown("Приоритет", priorityRus, listOf("Авто") + priorityMap.values.toList()) { priorityRus = it }

            Column {
                Text("Важность для вас: ${selfPriority.toInt()}", color = TextGray, style = MaterialTheme.typography.bodySmall)
                Slider(
                    value = selfPriority,
                    onValueChange = { selfPriority = it },
                    valueRange = 0f..10f,
                    steps = 9,
                    colors = SliderDefaults.colors(thumbColor = PrimaryBlue, activeTrackColor = PrimaryBlue)
                )
            }

            Column {
                Text("Влияние на день: ${influence.toInt()}", color = TextGray, style = MaterialTheme.typography.bodySmall)
                Slider(
                    value = influence,
                    onValueChange = { influence = it },
                    valueRange = 0f..10f,
                    steps = 9,
                    colors = SliderDefaults.colors(thumbColor = PrimaryBlue, activeTrackColor = PrimaryBlue)
                )
            }

            // Небольшой отступ снизу внутри скролла, чтобы последний слайдер не прилипал к кнопкам
            Spacer(modifier = Modifier.height(16.dp))
        }

        // Блок кнопок (фиксированный снизу)
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 16.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            OutlinedButton(
                onClick = onDismiss,
                modifier = Modifier.weight(1f).height(56.dp),
                shape = RoundedCornerShape(16.dp)
            ) {
                Text("Отмена")
            }

            Button(
                onClick = {
                    if (title.isBlank() || taskTypeRus.isBlank()) {
                        Toast.makeText(context, "Укажите название и категорию", Toast.LENGTH_SHORT).show()
                        return@Button
                    }

                    scope.launch(Dispatchers.IO) {
                        try {
                            val existingTasks = dao.getAllTasksOnce()
                            var foundDuplicate = false
                            if (description.isNotBlank()) {
                                for (existing in existingTasks) {
                                    if (calculateSimilarity(title, existing.title) >= 0.8 &&
                                        calculateSimilarity(description, existing.description ?: "") >= 0.8) {
                                        duplicateTaskInfo = existing.title
                                        foundDuplicate = true
                                        break
                                    }
                                }
                            }
                            if (foundDuplicate) {
                                withContext(Dispatchers.Main) { showDialog = true }
                            } else {
                                performSave()
                            }
                        } catch (e: Exception) {
                            withContext(Dispatchers.Main) {
                                Toast.makeText(context, "Ошибка сохранения", Toast.LENGTH_SHORT).show()
                            }
                        }
                    }
                },
                modifier = Modifier.weight(1f).height(56.dp),
                shape = RoundedCornerShape(16.dp),
                colors = ButtonDefaults.buttonColors(containerColor = PrimaryBlue)
            ) {
                Text("Создать", fontWeight = FontWeight.Bold, fontSize = 16.sp)
            }
        }
    }
}
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TaskDropdown(label: String, selected: String, options: List<String>, onSelect: (String) -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    ExposedDropdownMenuBox(expanded = expanded, onExpandedChange = { expanded = it }) {
        OutlinedTextField(
            value = selected, onValueChange = {}, readOnly = true,
            label = { Text(label) },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
            modifier = Modifier.menuAnchor().fillMaxWidth(),
            shape = RoundedCornerShape(12.dp)
        )
        ExposedDropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            options.forEach {
                DropdownMenuItem(text = { Text(it) }, onClick = { onSelect(it); expanded = false })
            }
        }
    }
}

suspend fun updateDailyStats(dao: TaskDao, today: LocalDate) {
    val stats = dao.findDailyStats(today)
    if (stats != null) {
        dao.updateDailyAdd(today, addTotal = 1, addInProgress = 1)
    } else {
        dao.insertDailyStats(
            DailyStatsEntity(
                date = today,
                totalTasks = 1,
                completedTasks = 0,
                overdueTasks = 0,
                inProgressTasks = 1
            )
        )
    }
}

fun calculateWorkingHours(now: LocalDateTime, deadline: LocalDateTime): Float {
    val WORK_START = 10
    val WORK_END = 18
    var totalHours = 0f
    var current = now

    if (current.isAfter(deadline)) return 0f

    while (current.isBefore(deadline)) {
        if (current.dayOfWeek.value in 1..5) {
            val startHour = max(current.hour, WORK_START)
            val endHour = if (current.toLocalDate() == deadline.toLocalDate()) {
                min(WORK_END, deadline.hour)
            } else {
                WORK_END
            }
            val diff = endHour - startHour
            if (diff > 0) totalHours += diff.toFloat()
        }
        current = current.plusDays(1).withHour(WORK_START).withMinute(0)
    }
    return totalHours
}