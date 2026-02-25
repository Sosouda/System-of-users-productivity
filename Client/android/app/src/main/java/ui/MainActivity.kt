package ui

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CalendarMonth
import androidx.compose.material.icons.filled.StackedLineChart
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.filled.Task
import androidx.compose.material.icons.outlined.CalendarMonth
import androidx.compose.material.icons.outlined.StackedLineChart
import androidx.compose.material.icons.outlined.Star
import androidx.compose.material.icons.outlined.Task
import androidx.compose.material3.*
import androidx.compose.material3.TabRowDefaults.tabIndicatorOffset
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.lifecycleScope
import api.AuthManager
import api.RetrofitClient
import data.TaskDao
import data.DailyStatsEntity
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.OffsetDateTime

class MainActivity : ComponentActivity() {

    private lateinit var dao: TaskDao

    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)

        RetrofitClient.initialize(this)

        val app = application as App
        dao = app.database.taskDao()

        val today = LocalDate.now()
        val now = OffsetDateTime.now()

        lifecycleScope.launch(Dispatchers.IO) {
            dao.updateTasksStatus(now)

            if (dao.findDailyStats(today) == null) {
                val yesterday = today.minusDays(1)
                val prevStats = dao.findDailyStats(yesterday)

                val inProgressTasks = prevStats?.inProgressTasks ?: dao.countActiveTasks()
                val overdueTasks = prevStats?.overdueTasks ?: dao.countOverdueTasks(now)

                dao.insertDailyStats(
                    DailyStatsEntity(
                        date = today,
                        totalTasks = inProgressTasks + overdueTasks,
                        completedTasks = 0,
                        overdueTasks = overdueTasks,
                        inProgressTasks = inProgressTasks
                    )
                )
            }
        }

        setContent {
            MaterialTheme {
                var isLoggedIn by remember {
                    mutableStateOf(AuthManager.isLoggedIn(this))
                }

                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = BackgroundColor
                ) {
                    if (!isLoggedIn) {
                        LoginScreen(onLoginSuccess = {
                            isLoggedIn = true
                        })
                    } else {
                        DrawTab(dao)
                    }
                }
            }
        }
    }
}

@Composable
fun DrawTab(dao: TaskDao) {
    var selectedTabIndex by remember { mutableIntStateOf(0) }
    val pagerState = rememberPagerState { tabItems.size }
    val scope = rememberCoroutineScope()

    LaunchedEffect(selectedTabIndex) {
        pagerState.animateScrollToPage(selectedTabIndex)
    }
    LaunchedEffect(pagerState.currentPage, pagerState.isScrollInProgress) {
        if (!pagerState.isScrollInProgress) {
            selectedTabIndex = pagerState.currentPage
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .statusBarsPadding()
    ) {
        Surface(
            color = SurfaceColor,
            tonalElevation = 4.dp,
            shadowElevation = 8.dp
        ) {
            TabRow(
                selectedTabIndex = selectedTabIndex,
                containerColor = SurfaceColor,
                contentColor = PrimaryBlue,
                divider = {},
                indicator = { tabPositions ->
                    if (selectedTabIndex < tabPositions.size) {
                        TabRowDefaults.SecondaryIndicator(
                            Modifier
                                .tabIndicatorOffset(tabPositions[selectedTabIndex])
                                .padding(horizontal = 12.dp)
                                .clip(RoundedCornerShape(topStart = 3.dp, topEnd = 3.dp)),
                            color = PrimaryBlue,
                            height = 3.dp
                        )
                    }
                }
            ) {
                tabItems.forEachIndexed { index, item ->
                    val selected = selectedTabIndex == index
                    Tab(
                        selected = selected,
                        onClick = { selectedTabIndex = index },
                        text = {
                            Text(
                                text = item.title,
                                fontSize = 10.sp,
                                fontWeight = if (selected) FontWeight.Bold else FontWeight.Medium,
                                maxLines = 1,
                                softWrap = false
                            )
                        },
                        icon = {
                            Icon(
                                imageVector = if (selected) item.sIcon else item.uIcon,
                                contentDescription = item.title,
                                tint = if (selected) PrimaryBlue else TextGray,
                                modifier = Modifier.size(20.dp)
                            )
                        }
                    )
                }
            }
        }

        HorizontalPager(
            state = pagerState,
            modifier = Modifier
                .fillMaxSize()
                .navigationBarsPadding(),
            beyondViewportPageCount = 1
        ) { index ->
            when (index) {
                0 -> DrawDashboard()
                1 -> DrawCalendar()
                2 -> DrawTaskList(dao)
                3 -> DrawStatisticScreen(dao)
            }
        }
    }
}

data class TabItem(
    val title: String,
    val uIcon: ImageVector,
    val sIcon: ImageVector
)

val tabItems = listOf(
    TabItem("Главная", Icons.Outlined.Star, Icons.Filled.Star),
    TabItem("Создать задачу", Icons.Outlined.CalendarMonth, Icons.Filled.CalendarMonth),
    TabItem("Список задач", Icons.Outlined.Task, Icons.Filled.Task),
    TabItem("Статистика", Icons.Outlined.StackedLineChart, Icons.Filled.StackedLineChart)
)