package api

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters

class SyncWorker(appContext: Context, workerParams: WorkerParameters) :
    CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        val (success, _) = SyncManager.runSync(applicationContext)

        return if (success) {
            Result.success()
        } else {
            Result.retry()
        }
    }
}