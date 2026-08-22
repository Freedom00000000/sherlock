package com.sherlock.android.model

data class SiteInfo(
    val name: String,
    val url: String,
    val urlMain: String,
    val errorType: String,
    val errorMsgs: List<String> = emptyList(),
    val regexCheck: String? = null,
    val requestHead: Boolean = false,
    val isDanishDating: Boolean = false
)
