package com.sherlock.android.service

import android.content.Context
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import com.sherlock.android.model.SiteInfo

private val DANISH_DATING_SITES = setOf(
    "DanishDatingNet", "DenmarkPassions", "Nydate"
)

class DataLoader(private val context: Context) {

    fun loadSites(): List<SiteInfo> {
        val json = context.assets.open("data.json")
            .bufferedReader()
            .use { it.readText() }

        val root = JsonParser.parseString(json).asJsonObject
        val sites = mutableListOf<SiteInfo>()

        for ((name, element) in root.entrySet()) {
            val obj = element as? JsonObject ?: continue
            val url = obj.get("url")?.asString ?: continue
            val urlMain = obj.get("urlMain")?.asString ?: continue
            val errorType = obj.get("errorType")?.asString ?: continue

            sites.add(
                SiteInfo(
                    name = name,
                    url = url,
                    urlMain = urlMain,
                    errorType = errorType,
                    errorMsg = obj.get("errorMsg")?.asString,
                    regexCheck = obj.get("regexCheck")?.asString,
                    requestHead = obj.get("request_head_only")?.asBoolean ?: false,
                    isDanishDating = name in DANISH_DATING_SITES
                )
            )
        }

        return sites.sortedWith(compareByDescending<SiteInfo> { it.isDanishDating }.thenBy { it.name })
    }
}
