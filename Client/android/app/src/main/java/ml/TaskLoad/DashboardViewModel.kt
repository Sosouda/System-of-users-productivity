package ml.TaskLoad

import android.content.Context
import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import data.TaskDao
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.time.OffsetDateTime

class DashboardViewModel(private val dao: TaskDao, context: Context) : ViewModel() {

    var capacityPercentage by mutableIntStateOf(0)
        private set

    private val predictor = TaskLoadPredictor(context)


    fun refreshCapacity() {
        viewModelScope.launch(Dispatchers.IO) {
            try {
                val activeTasks = dao.countActiveTasks()
                val overdueTasks = dao.countOverdueTasks(now=OffsetDateTime.now())

                if (activeTasks == 0 && overdueTasks == 0) {
                    withContext(Dispatchers.Main) { capacityPercentage = 0 }
                    return@launch
                }

                val avgPri = dao.getAvgPriority() ?: 0.0
                val maxPri = dao.getMaxPriority() ?: 0
                val avgHours = dao.getAvgHoursToDeadline(OffsetDateTime.now()) ?: 0.0

                val result = predictor.predictCapacity(
                    activeTasks = activeTasks,
                    avgPriority = avgPri.toFloat(),
                    maxPriority = maxPri,
                    avgHoursToDeadline = avgHours.toInt(),
                    overdueTasks = overdueTasks
                )

                withContext(Dispatchers.Main) {
                    capacityPercentage = result
                    Log.d("ML_DEBUG", "New value set: $capacityPercentage")
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    override fun onCleared() {
        super.onCleared()
        predictor.close()
    }
}
class DashboardViewModelFactory(
    private val dao: TaskDao,
    private val context: Context
) : ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        return DashboardViewModel(dao, context) as T
    }
}