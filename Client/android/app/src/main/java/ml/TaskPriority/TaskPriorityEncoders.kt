package ml.TaskPriority

data class LabelEncoder(
    val classes: List<String>
)

data class StandardScaler(
    val mean: List<Float>,
    val scale: List<Float>
)

data class TaskPriorityEncoders(
    val task_type_encoder: LabelEncoder,
    val priority_encoder: LabelEncoder,
    val hours_scaler: StandardScaler,
    val urgency_scaler: StandardScaler
)