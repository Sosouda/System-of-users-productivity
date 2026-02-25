package api

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.util.Log
import data.MainDb
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter

object AuthManager {
    private const val PREFS_NAME = "ProductivitySystemPrefs"
    private const val KEY_TOKEN = "token"
    private const val KEY_EXPIRY = "expiry"

    private fun getPrefs(context: Context): SharedPreferences {
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    }

    fun saveSession(context: Context, token: String, expiresAt: String? = null) {
        val expiryStr = expiresAt ?: OffsetDateTime.now().plusDays(30)
            .format(DateTimeFormatter.ISO_OFFSET_DATE_TIME)

        getPrefs(context).edit().apply {
            putString(KEY_TOKEN, token)
            putString(KEY_EXPIRY, expiryStr)
            apply()
        }
        Log.d("AUTH", "Сессия сохранена. Токен валиден до: $expiryStr")
    }

    fun getValidToken(context: Context): String? {
        val prefs = getPrefs(context)
        val token = prefs.getString(KEY_TOKEN, null)
        val expiryStr = prefs.getString(KEY_EXPIRY, null)

        if (token.isNullOrBlank() || expiryStr.isNullOrBlank()) {
            return null
        }

        return try {
            val expiryDate = OffsetDateTime.parse(expiryStr, DateTimeFormatter.ISO_OFFSET_DATE_TIME)
            if (OffsetDateTime.now().isAfter(expiryDate)) {
                Log.w("AUTH", "Срок действия токена истек")
                clearSession(context)
                null
            } else {
                token
            }
        } catch (e: Exception) {
            Log.e("AUTH", "Ошибка парсинга даты: ${e.message}")
            clearSession(context)
            null
        }
    }

    fun isLoggedIn(context: Context): Boolean {
        return getValidToken(context) != null
    }

    fun clearSession(context: Context) {
        getPrefs(context).edit().clear().apply()
        Log.d("AUTH", "Данные сессии стерты")
    }


    fun handleLogout(context: Context) {
        GlobalScope.launch(Dispatchers.Main) {
            try {
                val dataDir = context.applicationInfo.dataDir
                val sharedPrefsDir = java.io.File(dataDir, "shared_prefs")

                if (sharedPrefsDir.exists() && sharedPrefsDir.isDirectory) {
                    val list = sharedPrefsDir.list()
                    list?.forEach { fileName ->
                        val prefName = fileName.replace(".xml", "")
                        context.getSharedPreferences(prefName, Context.MODE_PRIVATE)
                            .edit()
                            .clear()
                            .commit()
                    }
                }

                withContext(Dispatchers.IO) {
                    try {
                        val db = MainDb.createDatabase(context)
                        db.clearAllTables()
                        db.close()
                        context.deleteDatabase("SPS.db")
                    } catch (e: Exception) {
                        Log.e("LOGOUT", "DB wipe error: ${e.message}")
                    }
                    RetrofitClient.reset()
                }

                val intent = context.packageManager.getLaunchIntentForPackage(context.packageName)
                if (intent != null) {
                    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
                    context.startActivity(intent)

                    if (context is Activity) {
                        context.finishAffinity()
                    }

                    delay(300)
                    android.os.Process.killProcess(android.os.Process.myPid())
                }
            } catch (e: Exception) {
                Log.e("LOGOUT", "Logout process failed: ${e.message}")
            }
        }
    }
}