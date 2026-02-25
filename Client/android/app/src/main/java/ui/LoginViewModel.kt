package ui

import android.content.Context
import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import api.AuthManager
import api.RetrofitClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter

class LoginViewModel : ViewModel() {

    var email by mutableStateOf("")
    var password by mutableStateOf("")


    var isRegisterMode by mutableStateOf(false)
    var isLoading by mutableStateOf(false)
    var errorMessage by mutableStateOf<String?>(null)

    fun onActionClick(context: Context, onSuccess: () -> Unit) {
        if (isRegisterMode) {
            onRegisterClick(context, onSuccess)
        } else {
            onLoginClick(context, onSuccess)
        }
    }

    fun onLoginClick(context: Context, onSuccess: () -> Unit) {
        if (email.isBlank() || password.isBlank()) {
            errorMessage = "Введите логин и пароль"
            return
        }

        viewModelScope.launch {
            isLoading = true
            errorMessage = null
            try {
                val response = RetrofitClient.instance.login(email, password)

                if (response.isSuccessful) {
                    val body = response.body()
                    if (body != null) {
                        val tokenValue = body.access_token

                        val expiryDate = OffsetDateTime.now()
                            .plusDays(30)
                            .format(DateTimeFormatter.ISO_OFFSET_DATE_TIME)

                        AuthManager.saveSession(context, tokenValue, expiryDate)

                        RetrofitClient.reset()

                        withContext(Dispatchers.IO) {
                            val syncPrefs = context.getSharedPreferences("sync_prefs", Context.MODE_PRIVATE)
                            syncPrefs.edit().clear().commit()
                        }

                        Log.d("LOGIN", "Вход выполнен успешно, токен сохранен")
                        onSuccess()
                    } else {
                        errorMessage = "Сервер прислал пустой ответ"
                    }
                } else {
                    errorMessage = "Неверный логин или пароль (код: ${response.code()})"
                }
            } catch (e: Exception) {
                Log.e("LOGIN_ERROR", "Error during login: ${e.message}")
                errorMessage = "Ошибка соединения: ${e.localizedMessage}"
            } finally {
                isLoading = false
            }
        }
    }
    fun onRegisterClick(context: Context, onSuccess: () -> Unit) {
        if (email.isBlank() || password.isBlank()) {
            errorMessage = "Заполните все поля"
            return
        }

        viewModelScope.launch {
            isLoading = true
            errorMessage = null
            try {
                val userMap = mapOf(
                    "email" to email,
                    "password" to password
                )

                val response = RetrofitClient.instance.register(userMap)

                if (response.isSuccessful) {
                    Log.d("REGISTER", "Регистрация успешна, входим...")
                    onLoginClick(context, onSuccess)
                } else {
                    val errorJson = response.errorBody()?.string()
                    errorMessage = "Ошибка: $errorJson"
                }
            } catch (e: Exception) {
                errorMessage = "Сеть недоступна: ${e.localizedMessage}"
            } finally {
                isLoading = false
            }
        }
    }
}