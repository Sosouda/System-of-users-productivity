package ui

import android.app.Application
import android.content.Context
import android.util.Log
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkRequest
import api.SyncWorker
import data.MainDb
import java.util.concurrent.TimeUnit


class App : Application() {

    val database by lazy { MainDb.createDatabase(this) }

    override fun onCreate() {
        super.onCreate()

        val dbPath = database.openHelper.readableDatabase.path
        Log.d("DB_PATH", "Path = $dbPath")

        scheduleSync(this)
    }

    private fun scheduleSync(context: Context) {
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()

        val syncRequest = PeriodicWorkRequestBuilder<SyncWorker>(15, TimeUnit.MINUTES)
            .setConstraints(constraints)
            .setBackoffCriteria(
                BackoffPolicy.LINEAR,
                WorkRequest.MIN_BACKOFF_MILLIS,
                TimeUnit.MILLISECONDS
            )
            .build()

        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
            "AutoSyncTasks",
            ExistingPeriodicWorkPolicy.KEEP,
            syncRequest
        )

        Log.d("SYNC", "WorkManager: Фоновая синхронизация запланирована")
    }
}