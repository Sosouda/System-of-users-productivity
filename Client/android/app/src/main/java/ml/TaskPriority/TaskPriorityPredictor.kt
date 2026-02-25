package ml.TaskPriority

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import android.content.Context
import com.google.gson.Gson
import java.nio.FloatBuffer
import ai.onnxruntime.OrtException

class TaskPriorityPredictor(context: Context) : AutoCloseable {

    private val MODEL_NAME = "dualhead_tpm_embedded.onnx"
    private val ENCODERS_NAME = "dualhead_tpm_encoders.json"

    private val env: OrtEnvironment = OrtEnvironment.getEnvironment()
    private val session: OrtSession
    private val encoders: TaskPriorityEncoders

    init {
        val modelBytes = context.assets.open(MODEL_NAME).use { it.readBytes() }
        session = env.createSession(modelBytes)

        val json = context.assets.open(ENCODERS_NAME).bufferedReader().use { it.readText() }

        val tempEncoders = Gson().fromJson(json, TaskPriorityEncoders::class.java)

        if (tempEncoders.task_type_encoder == null) {
            throw OrtException("JSON Error: task_type_encoder не найден или имеет неверный формат. Проверьте JSON-файл.")
        }
        if (tempEncoders.priority_encoder == null) {
            throw OrtException("JSON Error: priority_encoder не найден или имеет неверный формат. Проверьте JSON-файл.")
        }

        encoders = tempEncoders
    }


    private fun encodeLabel(label: String, encoder: LabelEncoder): FloatArray {
        val array = FloatArray(encoder.classes.size)
        val index = encoder.classes.indexOf(label)
        if (index >= 0) array[index] = 1f
        return array
    }

    private fun scaleValue(value: Float, scaler: StandardScaler): FloatArray {
        return FloatArray(1) {
            if (scaler.scale.isNotEmpty() && scaler.scale[0] != 0f) {
                (value - scaler.mean[0]) / scaler.scale[0]
            } else {
                0.0f
            }
        }
    }


    fun predict(taskType: String, hoursLeft: Float, urgency: Float): String {
        val taskTypeEncoded = encodeLabel(taskType, encoders.task_type_encoder)
        val hoursScaled = scaleValue(hoursLeft, encoders.hours_scaler)
        val urgencyScaled = scaleValue(urgency, encoders.urgency_scaler)

        val input1Array = taskTypeEncoded + hoursScaled
        val tensor1 = OnnxTensor.createTensor(
            env,
            FloatBuffer.wrap(input1Array),
            longArrayOf(1, input1Array.size.toLong())
        )

        val tensor2 = OnnxTensor.createTensor(
            env,
            FloatBuffer.wrap(urgencyScaled),
            longArrayOf(1, urgencyScaled.size.toLong())
        )

        return env.use {
            session.run(mapOf("input1" to tensor1, "input2" to tensor2)).use { result ->
                val logits = result[0].value as Array<FloatArray>

                val predIdx = logits[0].indices.maxByOrNull { logits[0][it] } ?: 0

                encoders.priority_encoder.classes[predIdx]
            }
        }
    }

    override fun close() {
        session.close()
        env.close()
    }
}