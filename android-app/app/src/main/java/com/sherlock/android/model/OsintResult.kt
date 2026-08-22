package com.sherlock.android.model

data class OsintResult(
    val platform: String,
    val found: Boolean,
    val url: String?,
    val details: List<String> = emptyList()
)
