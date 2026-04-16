package com.sherlock.android.model

enum class ResultStatus { FOUND, NOT_FOUND, ERROR }

data class CheckResult(
    val siteName: String,
    val url: String,
    val status: ResultStatus,
    val errorMessage: String? = null,
    val isDanishDating: Boolean = false
)
