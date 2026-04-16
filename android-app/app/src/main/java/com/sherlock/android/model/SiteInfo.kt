package com.sherlock.android.model

data class SiteInfo(
    val name: String,
    val url: String,
    val urlMain: String,
    val errorType: String,
    val errorMsg: String? = null,
    val regexCheck: String? = null,
    val requestHead: Boolean = false,
    val isDanishDating: Boolean = false
)
