package ui

import android.util.Log
import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Info
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
import data.TaskDao
import data.TaskEntity
import data.TitleDesc
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.time.LocalDate
import java.time.OffsetDateTime
import java.time.ZoneOffset


val taskTypeTranslations = mapOf(
    "Dust Cleaning" to "Уборка пыли",
    "Meeting" to "Встреча",
    "Documentation" to "Документация",
    "Customer Support" to "Поддержка клиентов",
    "Code Bug Fix" to "Исправление багов",
    "Research" to "Исследование",
    "Feature Development" to "Разработка фич",
    "Optimization" to "Оптимизация",
    "Deployment" to "Деплой",
    "Project Management" to "Управление проектом",
    "Other" to "Другое"
)

val priorityTranslations = mapOf(
    "Casual" to "Обычный",
    "Low" to "Низкий",
    "Mid" to "Средний",
    "High" to "Высокий",
    "Extreme" to "Критический"
)

@Composable
fun DrawTaskList(dao: TaskDao) {
    var showTaskDialog by remember { mutableStateOf(false) }
    var selectedTask by remember { mutableStateOf<TaskEntity?>(null) }
    val tasks by dao.selectTasksForInventory().collectAsState(initial = emptyList())

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(BackgroundColor)
            .padding(16.dp)
    ) {
        Text(
            text = "Список задач",
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold,
            color = TextDark
        )
        Text(
            text = "Управляйте задачами индивидуально",
            style = MaterialTheme.typography.bodyMedium,
            color = TextGray,
            modifier = Modifier.padding(bottom = 24.dp)
        )

        if (tasks.isEmpty()) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("Нет активных задач", color = TextGray)
            }
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                verticalArrangement = Arrangement.spacedBy(12.dp),
                contentPadding = PaddingValues(bottom = 80.dp)
            ) {
                items(tasks) { taskEntity ->
                    TaskInventoryItem(
                        task = TitleDesc(title = taskEntity.title, description = taskEntity.description ?: ""),
                        onClick = {
                            selectedTask = taskEntity
                            showTaskDialog = true
                        }
                    )
                }
            }
        }
    }

    if (showTaskDialog && selectedTask != null) {
        Dialog(onDismissRequest = { showTaskDialog = false }) {
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .fillMaxHeight(0.85f),
                shape = RoundedCornerShape(28.dp),
                color = BackgroundColor
            ) {
                TaskDetailDialog(
                    dao = dao,
                    taskId = selectedTask!!.id,
                    taskName = selectedTask!!.title,
                    taskDescription = selectedTask!!.description ?: "",
                    onDismiss = { showTaskDialog = false }
                )
            }
        }
    }
}

@Composable
fun TaskInventoryItem(task: TitleDesc, onClick: () -> Unit) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        color = SurfaceColor,
        tonalElevation = 1.dp,
        onClick = onClick
    ) {
        Row(modifier = Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .background(PrimaryBlue.copy(alpha = 0.1f), RoundedCornerShape(12.dp)),
                contentAlignment = Alignment.Center
            ) {
                Icon(Icons.Default.Edit, contentDescription = null, tint = PrimaryBlue, modifier = Modifier.size(20.dp))
            }
            Column(modifier = Modifier.padding(start = 16.dp).weight(1f)) {
                Text(text = task.title, fontWeight = FontWeight.Bold, color = TextDark, fontSize = 16.sp)
                Text(text = task.description, color = TextGray, fontSize = 13.sp, maxLines = 1)
            }
            Icon(Icons.Default.Info, contentDescription = null, tint = TextGray.copy(alpha = 0.5f))
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TaskDetailDialog(
    taskId: String,
    taskName: String,
    taskDescription: String,
    dao: TaskDao,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    val scrollState = rememberScrollState()

    var taskTypeEng by remember { mutableStateOf("Other") }
    var taskDeadline by remember { mutableStateOf("") }
    var taskPriorityEng by remember { mutableStateOf("Mid") }
    var isCompleted by remember { mutableStateOf(false) }

    val priorityMap = mapOf("Casual" to 1, "Low" to 2, "Mid" to 3, "High" to 4, "Extreme" to 5)

    LaunchedEffect(taskId) {
        val task = dao.selectTaskById(taskId)
        task?.let {
            taskDeadline = it.deadline?.toLocalDate()?.toString() ?: ""
            isCompleted = it.status == "completed"

            taskPriorityEng = priorityMap.entries.find { entry ->
                entry.value.toString() == it.finalPriority || entry.key == it.finalPriority
            }?.key ?: "Mid"

            taskTypeEng = dao.getTaskTypeNameById(it.taskTypeId) ?: "Other"
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Text("Редактирование", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)

        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(PrimaryBlue.copy(0.05f), RoundedCornerShape(12.dp))
                .padding(12.dp)
        ) {
            Text(taskName, fontWeight = FontWeight.Bold, color = PrimaryBlue)
            Text(taskDescription, fontSize = 14.sp, color = TextGray)
        }

        TaskDropdown(
            label = "Тип задачи",
            selected = taskTypeTranslations[taskTypeEng] ?: taskTypeEng,
            options = taskTypeTranslations.values.toList()
        ) { selectedRus ->
            taskTypeEng = taskTypeTranslations.filterValues { it == selectedRus }.keys.firstOrNull() ?: "Other"
        }

        OutlinedTextField(
            value = taskDeadline,
            onValueChange = { taskDeadline = it },
            label = { Text("Дедлайн (ГГГГ-ММ-ДД)") },
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp)
        )

        TaskDropdown(
            label = "Приоритет",
            selected = priorityTranslations[taskPriorityEng] ?: taskPriorityEng,
            options = priorityTranslations.values.toList()
        ) { selectedRus ->
            taskPriorityEng = priorityTranslations.filterValues { it == selectedRus }.keys.firstOrNull() ?: "Mid"
        }

        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            color = if (isCompleted) SuccessGreen.copy(0.1f) else Color.Transparent,
            border = androidx.compose.foundation.BorderStroke(1.dp, if (isCompleted) SuccessGreen else TextGray.copy(0.3f))
        ) {
            Row(
                modifier = Modifier
                    .clickable { isCompleted = !isCompleted }
                    .padding(16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    Icons.Default.CheckCircle,
                    contentDescription = null,
                    tint = if (isCompleted) SuccessGreen else TextGray.copy(0.3f)
                )
                Spacer(Modifier.width(12.dp))
                Text(
                    text = if (isCompleted) "Выполнено" else "В процессе",
                    color = if (isCompleted) SuccessGreen else TextDark,
                    fontWeight = FontWeight.Medium
                )
                Spacer(Modifier.weight(1f))
                Switch(
                    checked = isCompleted,
                    onCheckedChange = { isCompleted = it },
                    colors = SwitchDefaults.colors(checkedThumbColor = SuccessGreen)
                )
            }
        }

        Spacer(Modifier.height(8.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            OutlinedButton(
                onClick = onDismiss,
                modifier = Modifier.weight(1f).height(50.dp),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("Отмена")
            }

            Button(
                onClick = {
                    scope.launch(Dispatchers.IO) {
                        try {
                            val typeId = dao.getTaskTypeIdByName(taskTypeEng) ?: 9
                            val now = OffsetDateTime.now(ZoneOffset.UTC)

                            val deadlineParsed = try {
                                LocalDate.parse(taskDeadline).atStartOfDay(ZoneOffset.UTC).toOffsetDateTime()
                            } catch (e: Exception) {
                                now.plusDays(1)
                            }

                            val priorityInt = priorityMap[taskPriorityEng] ?: 3

                            dao.updateTaskPropertiesById(
                                id = taskId,
                                deadline = deadlineParsed,
                                status = if (isCompleted) "completed" else "underway",
                                priority = priorityInt,
                                taskTypeId = typeId,
                                updatedAt = now
                            )

                            val today = LocalDate.now()
                            val completedCount = dao.countCompletedTasksByDate(today.toString())
                            dao.upsertCompletedStats(today, completedCount)

                            withContext(Dispatchers.Main) {
                                Toast.makeText(context, "Изменения сохранены", Toast.LENGTH_SHORT).show()
                                onDismiss()
                            }
                        } catch (e: Exception) {
                            Log.e("SAVE_ERROR", "Error: ${e.message}")
                        }
                    }
                },
                modifier = Modifier.weight(1f).height(50.dp),
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(containerColor = PrimaryBlue)
            ) {
                Text("Сохранить")
            }
        }
    }
}